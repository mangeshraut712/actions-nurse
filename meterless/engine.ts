// H-MEM loader for Actions Nurse. `npm run setup` vendors the actual Meterless
// reference engine; we intentionally do not provide a fallback implementation.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const CANDIDATES = [
  {
    label: "vendor/hmem",
    entry: path.join(here, "vendor", "hmem", "src", "index.ts"),
  },
  {
    label: "monorepo sibling",
    entry: path.join(here, "..", "..", "..", "engines", "hmem", "reference", "src", "index.ts"),
  },
];

export interface LoadedEngine {
  HMEM: new (opts: { clock?: () => number; persistDir?: string }) => any;
  source: string;
}

export async function loadHMEM(): Promise<LoadedEngine> {
  for (const candidate of CANDIDATES) {
    if (fs.existsSync(candidate.entry)) {
      const mod = await import(pathToFileURL(candidate.entry).href);
      if (typeof mod.HMEM !== "function") {
        throw new Error(`H-MEM source at ${candidate.entry} did not export HMEM`);
      }
      return { HMEM: mod.HMEM, source: candidate.label };
    }
  }
  throw new Error(
    "H-MEM engine not found. From meterless/, run `npm install && npm run setup` to vendor it.",
  );
}
