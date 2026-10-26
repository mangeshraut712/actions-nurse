#!/usr/bin/env node
/**
 * Actions Nurse's real Meterless H-MEM bridge.
 *
 * Human use:
 *   npm run memory -- seed
 *   npm run memory -- ask "why did TypeScript CI fail?"
 *   npm run memory -- remember '{"failing_step":"...","root_cause":"..."}' --json
 *
 * Machine use keeps stdout as a single JSON object. Pass a JSON payload on
 * stdin for `remember` or `ask`, e.g.:
 *   printf '%s' '{"query":"previous disk failures"}' | npm run memory -- ask --json
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadHMEM } from "./engine.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_STATE_DIR = path.join(here, ".nurse-memory");
const MAX_TEXT = 1_600;
const SECRET_PATTERNS = [
  /\b(?:ghp|github_pat|gho|ghu|ghs)_[A-Za-z0-9_\-]+\b/g,
  /\bBearer\s+[^\s,;]+/gi,
  /\b(?:Bearer|token|password|api[_ -]?key)\s*[:=]\s*[^\s,;]+/gi,
];

type Json = Record<string, unknown>;

function cleanText(value: unknown, limit = MAX_TEXT): string {
  let text = String(value ?? "").replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, " ").trim();
  for (const pattern of SECRET_PATTERNS) text = text.replace(pattern, "[redacted]");
  return text.slice(0, limit);
}

function option(args: string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : undefined;
}

function nonFlags(args: string[]): string[] {
  const result: string[] = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i].startsWith("--")) {
      if (args[i] !== "--json" && args[i] !== "--preview") i += 1;
      continue;
    }
    result.push(args[i]);
  }
  return result;
}

async function stdinText(): Promise<string> {
  if (process.stdin.isTTY) return "";
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) chunks.push(Buffer.from(chunk));
  return Buffer.concat(chunks).toString("utf-8").trim();
}

async function inputPayload(args: string[]): Promise<Json> {
  const supplied = nonFlags(args).join(" ").trim();
  const raw = supplied || await stdinText();
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    return typeof parsed === "object" && parsed !== null && !Array.isArray(parsed)
      ? parsed as Json
      : { content: raw };
  } catch {
    return { content: raw };
  }
}

function compactMemory(item: any): Json {
  const memory = item?.memory ?? item ?? {};
  return {
    id: cleanText(memory.id, 160),
    content: cleanText(memory.content),
    type: cleanText(memory.type, 120),
    layer: cleanText(memory.layer, 120),
    source: cleanText(memory.source, 200),
    relevance: typeof item?.relevance === "number" ? Number(item.relevance.toFixed(4)) : undefined,
  };
}

function diagnosisText(payload: Json): string {
  const supplied = cleanText(payload.content ?? payload.diagnosis ?? "");
  if (supplied) return supplied;
  const step = cleanText(payload.failing_step ?? "Unknown step", 200);
  const cause = cleanText(payload.root_cause ?? "Unspecified CI failure", 800);
  const patterns = Array.isArray(payload.patterns)
    ? payload.patterns.map((value) => cleanText(value, 180)).filter(Boolean).join(", ")
    : "";
  const fixture = cleanText((payload.provenance as Json | undefined)?.fixture ?? payload.fixture ?? "", 160);
  return [
    "Actions Nurse CI diagnosis.",
    `Failing step: ${step}.`,
    `Root cause: ${cause}.`,
    patterns ? `Matched patterns: ${patterns}.` : "",
    fixture ? `Fixture: ${fixture}.` : "",
  ].filter(Boolean).join(" ");
}

function provenance(payload: Json): string {
  const nested = payload.provenance;
  const fixture = cleanText(
    (nested && typeof nested === "object" && !Array.isArray(nested) ? (nested as Json).fixture : undefined)
      ?? payload.fixture
      ?? "triage",
    120,
  );
  return `actions-nurse:${fixture || "triage"}`;
}

async function remember(hmem: any, payload: Json): Promise<Json> {
  const content = diagnosisText(payload);
  if (!content) throw new Error("remember needs a diagnosis payload or text");

  // MemoryMiningService: actual H-MEM model-free extraction path. The event
  // name is part of H-MEM's public contract; keep triage provenance in the
  // mined text as well as in this command's response.
  const mined = await hmem.mine(
    "chat_message",
    `Remember this Actions Nurse diagnosis from ${provenance(payload)}: ${content}`,
  );
  const records = Array.isArray(mined) ? mined : [];
  if (records.length > 0) {
    // Preserve the fixture/triage provenance on the actual memory record too.
    // This goes through H-MEM's real MemoryStoreService and ledger, rather
    // than keeping provenance only in the subprocess response.
    const source = provenance(payload);
    const stored = records.map((record: any) => hmem.store.update(record.id, {
      source,
      provenance: {
        origin: "chat_message",
        learnedAt: Date.now(),
        label: `Actions Nurse diagnosis from ${source}`,
      },
    }));
    return {
      operation: "remember",
      service: "MemoryMiningService",
      stored: stored.map(compactMemory),
      provenance: source,
      redacted: content,
    };
  }

  // MemoryStoreService direct capture keeps an unusual but valid diagnosis
  // searchable when the mining heuristic finds no extractable proposition.
  const record = hmem.add({
    content,
    type: "factual",
    source: provenance(payload),
  });
  return {
    operation: "remember",
    service: "MemoryMiningService + MemoryStoreService",
    stored: [compactMemory(record)],
    provenance: provenance(payload),
    redacted: content,
  };
}

async function ask(hmem: any, payload: Json): Promise<Json> {
  const query = cleanText(payload.query ?? payload.content ?? "", 500);
  if (!query) throw new Error("ask needs a query");
  // MemoryRetrievalService: H-MEM hybrid ranking and reinjection context.
  const result = hmem.query(query, { threshold: 0.1 });
  const memories = Array.isArray(result?.memories) ? result.memories.map(compactMemory) : [];
  return {
    operation: "ask",
    service: "MemoryRetrievalService",
    query,
    memories,
    memory_ids: memories.map((memory) => memory.id).filter(Boolean),
    context: cleanText(result?.context, 3_000),
    strategy: cleanText(result?.trace?.strategy, 200),
  };
}

async function seed(hmem: any): Promise<Json> {
  const seedPath = path.join(here, "seed", "ci-failures.txt");
  const entries = fs.readFileSync(seedPath, "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"));
  const stored: Json[] = [];
  for (const entry of entries) {
    // Call the same MemoryMiningService path the live bridge uses.
    const result = await remember(hmem, { content: entry, provenance: { fixture: "seed" } });
    const rows = result.stored;
    if (Array.isArray(rows)) stored.push(...rows as Json[]);
  }
  return {
    operation: "seed",
    service: "MemoryMiningService + MemoryStoreService",
    seed_file: path.relative(here, seedPath),
    stored,
    count: stored.length,
  };
}

async function audit(hmem: any, payload: Json): Promise<Json> {
  const id = cleanText(payload.id ?? payload.memory_id ?? payload.content ?? "", 160);
  if (!id) throw new Error("audit needs a memory id");
  // TrustLedgerService: H-MEM's append-only per-memory history.
  const history = hmem.ledger.history(id);
  return {
    operation: "audit",
    service: "TrustLedgerService",
    memory_id: id,
    history: Array.isArray(history) ? history.map((event: any) => ({
      action: cleanText(event?.action, 120),
      actor: cleanText(event?.actor, 120),
      timestamp: typeof event?.timestamp === "number" ? new Date(event.timestamp).toISOString() : cleanText(event?.timestamp, 80),
      previous_confidence: event?.previousState?.confidence,
      new_confidence: event?.newState?.confidence,
    })) : [],
  };
}

async function sleep(hmem: any, previewOnly: boolean): Promise<Json> {
  // SleepCycleService: preview-first consolidation and backup guardrail.
  const preview = hmem.sleep.preview();
  const summary = {
    consolidate: Array.isArray(preview?.toConsolidate) ? preview.toConsolidate.length : 0,
    archive: Array.isArray(preview?.toArchive) ? preview.toArchive.length : 0,
    synthesize: Array.isArray(preview?.toSynthesize) ? preview.toSynthesize.length : 0,
  };
  if (previewOnly) {
    return { operation: "sleep", service: "SleepCycleService", preview: true, plan: summary };
  }
  const report = hmem.sleep.execute(preview);
  return {
    operation: "sleep",
    service: "SleepCycleService",
    preview: false,
    plan: summary,
    backup_id: cleanText(report?.backupId, 160),
  };
}

function usage(): string {
  return `Actions Nurse H-MEM bridge (real Meterless engine)

  npm run memory -- seed
  npm run memory -- remember '<diagnosis text>'
  printf '%s' '{"failing_step":"Build / bundler","root_cause":"Node OOM","fixture":"oom-killed.txt"}' | npm --silent run memory -- remember --json
  npm run memory -- ask "have we seen a runner disk failure?"
  npm run memory -- audit mem-1
  npm run memory -- sleep --preview

Add --json for one machine-readable JSON object on stdout.`;
}

async function main(): Promise<void> {
  const [command = "help", ...args] = process.argv.slice(2);
  const jsonMode = args.includes("--json");
  const stateDir = path.resolve(process.env.NURSE_HMEM_DIR || DEFAULT_STATE_DIR);
  fs.mkdirSync(stateDir, { recursive: true });
  const { HMEM, source } = await loadHMEM();
  const hmem = new HMEM({ persistDir: stateDir });

  let result: Json;
  if (command === "remember") result = await remember(hmem, await inputPayload(args));
  else if (command === "ask") {
    const payload = await inputPayload(args);
    result = await ask(hmem, {
      ...payload,
      query: option(args, "--query") ?? payload.query ?? payload.content,
    });
  } else if (command === "seed") result = await seed(hmem);
  else if (command === "audit") {
    const payload = await inputPayload(args);
    const suppliedId = nonFlags(args).join(" ");
    result = await audit(hmem, {
      ...payload,
      id: option(args, "--id") || suppliedId || payload.id || payload.memory_id || payload.content,
    });
  } else if (command === "sleep") result = await sleep(hmem, args.includes("--preview"));
  else {
    if (jsonMode) console.log(JSON.stringify({ ok: false, error: "unknown command", usage: usage() }));
    else console.log(usage());
    process.exitCode = command === "help" ? 0 : 2;
    return;
  }

  const output = {
    ok: true,
    engine_source: source,
    state_dir: path.relative(here, stateDir) || ".",
    ...result,
  };
  if (jsonMode) {
    console.log(JSON.stringify(output));
  } else {
    console.log(`engine source: ${source} | state: ${output.state_dir}`);
    console.log(JSON.stringify(output, null, 2));
  }
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`H-MEM bridge error: ${message}`);
  process.exit(1);
});
