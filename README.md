# Actions Nurse

**Hacktoberfest Hack Day Pune x Cloud Native Pune** · powered by open-weight **Gemma 4**

Paste a failed GitHub Actions log (or a red CI screenshot) → get failing step, root cause, suggested fix, and confidence.

| Mode | When |
|---|---|
| **Gemma 4** (`gemma-4-26b-a4b-it`) | `GEMINI_API_KEY` set |
| **Rules** | No key — tsc / pytest / OOM / npm patterns |

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=your_key   # optional
uvicorn nurse:app --host 127.0.0.1 --port 8787
# http://127.0.0.1:8787
```

## MLH challenges
- Best Use of Gemma 4
- Best Open-Source AI Project

## License
MIT
