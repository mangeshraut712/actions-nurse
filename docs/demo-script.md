# 🎤 Actions Nurse — 2–3 Minute Show-and-Tell Script

**Audience**: MLH Judges & Hacktoberfest Hack Day Pune x Cloud Native Pune  
**Time Limit**: 2–3 Minutes  
**Focus**: Problem Statement → Gemma 4 + Rules Architecture → Live Demo → Hackathon Impact  

---

### [0:00 – 0:35] The Hook & Problem Statement
> *"Hey everyone! We're thrilled to present **Actions Nurse** for Hacktoberfest Hack Day Pune x Cloud Native Pune.*  
>  
> *If you work in cloud-native or software engineering, you know the dread of a red GitHub Actions build. You click through layers of logs, scrolling through 4,000 lines of noise just to figure out what broke and how to fix it.*  
>  
> *Actions Nurse is a lightweight, open-source triage assistant that turns noisy CI logs into structured, instant diagnoses powered by **Gemma 4**."*

---

### [0:35 – 1:30] Live Demo: Quick Triage & Resilience

**Action 1**: Open `http://127.0.0.1:8787`.
> *"Notice the interface: clean, responsive, and ready out of the box. Notice the top badge indicates our status."*

**Action 2**: Click **Load red screenshot demo**.
> *"This is a realistic red Actions run: checkout failed because the runner cannot read a repository username. One click loads both the screenshot and its matching sanitized log — so this is a genuine multimodal Gemma 4 request, not an image pasted into slides."*
>
> *"I click **Triage with Gemma 4**. The result keeps the evidence separate from the recommendation: failing step, root cause, suggested fix, confidence, engine badge, and copyable commands."*
>
> *"If this demo has no key or network, notice it says **Rules** instead of claiming Gemma. That transparent fallback still identifies checkout/repository access and tells us to verify the token or deploy key without exposing credentials."*

**Action 3**: Click the `npm-typecheck` fixture button.
> *"Let's test an everyday team headache: someone merged a PR with mismatched TypeScript exports. I click `npm-typecheck.txt`, which loads a real CI failure, and click **Triage with Gemma 4**."*  
> *(Show results on screen)*  
> *"Instantly, Actions Nurse isolates:*  
> - *Failing Step: `Typecheck / tsc`*  
> - *Root Cause: Module missing exported members after a merge*  
> - *Suggested Fix: Align exports or rebase onto main*  
> - *Confidence: High."*

**Action 4**: Click `oom-killed`.
> *"Now let's try an infrastructure error: Node.js running out of heap memory during bundling (`Exit Code 134`).*  
> *(Click Triage)*  
> *"Actions Nurse immediately spots the OOM kill and offers the exact environment fix: increasing `NODE_OPTIONS=--max-old-space-size=4096` in the GitHub Actions workflow YAML."*

---

### [1:30 – 2:15] Gemma 4 & Offline Reliability

> *"Under the hood, this is deliberately Gemma-first. With `GEMINI_API_KEY`, the app sends the log — and, when attached, the screenshot — to **Gemma 4** first. We require structured JSON so the output is a diagnosis plus reviewable commands, not a vague chatbot answer.*
>
> *The visible 12-second budget is intentional: if the key, network, or model response is unavailable, the deterministic rules engine returns a clearly labeled answer. That makes the demo resilient without pretending the fallback is Gemma."*

**Action 5 (optional, 15 seconds):** Click **Compare Rules vs Gemma** on the same fixture.
> *"This is our proof surface: the left card is an offline deterministic baseline; the right card is Gemma 4's contextual result when the key is available. Same evidence, provenance visible, and no model claim when it is unavailable."*

---

### [2:15 – 2:45] Open Source & Prize Targets

> *"Why this matters for Cloud Native Pune:*  
> *In Kubernetes and CI/CD pipelines, engineers need actionable feedback, fast. Actions Nurse is 100% open-source under the MIT license with a zero-friction FastAPI + vanilla JS stack. It also ships as a composite GitHub Action that collects failed-step logs, writes the job summary, and preserves a markdown report artifact.*
>  
> *We are targeting:*  
> - **Best Use of Gemma 4**: Applying lightweight, open-weight code models to developer productivity workflows.  
> - **Best Open-Source AI Project**: Zero lock-in, reliable offline fallback, and practical utility for every developer.*  
>  
> *Check out the repo on GitHub: `mangeshraut712/actions-nurse`. Thank you!"*
