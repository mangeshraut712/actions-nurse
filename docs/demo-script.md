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

### [0:35 – 1:35] Live Demo: Checkout Auth + Multimodal Compare

**Action 1**: Open `http://127.0.0.1:8787`.
> *"Notice the interface: clean, responsive, and ready out of the box. Notice the top badge indicates our status."*

**Action 2**: Click **Load red screenshot demo**.
> *"This is a realistic red Actions run: checkout failed because the runner cannot read a repository username. One click loads both the bundled screenshot and its matching sanitized `checkout-auth` log. With a Gemma-enabled local run, triage sends both parts together to `/api/triage-image` — a genuine multimodal request, not an image pasted into slides."*
>
> *"I click **Triage with Gemma 4**. The result keeps the evidence separate from the recommendation: failing step, root cause, suggested fix, confidence, engine badge, and copyable commands."*
>
> *"If the runtime has no key, no network, or rules-only mode is enabled, notice it says **Rules** instead of claiming Gemma. That transparent fallback still identifies checkout/repository access and tells us to verify the token or deploy key without exposing credentials."*

**Action 3**: With the screenshot and auth log still loaded, click **Compare Rules vs Gemma**.
> *"Now the comparison shows input provenance. The deterministic rules baseline reads the log; when Gemma runs, it gets that same log plus the screenshot. The model name appears with its result. If the runtime skips or cannot reach Gemma, it says why and the rules diagnosis remains visible."*

*(If there is time, click a fixture chip to show the reproducible failures. Choosing a text fixture clears the screenshot so the inputs cannot be mixed accidentally.)*

---

### [1:35 – 2:20] Gemma 4 & Offline Reliability

> *"Under the hood, this is deliberately Gemma-first. With `GEMINI_API_KEY` configured and rules-only mode disabled, the app sends the log — and, when attached, the screenshot — to **Gemma 4** first. We require structured JSON so the output is a diagnosis plus reviewable commands, not a vague chatbot answer.*
>
> *The visible 12-second budget is intentional: if the key, network, or model response is unavailable, the deterministic rules engine returns a clearly labeled answer. That makes the demo resilient without pretending the fallback is Gemma."*

---

### [2:20 – 2:50] Open Source & Prize Targets

> *"Why this matters for Cloud Native Pune:*  
> *In Kubernetes and CI/CD pipelines, engineers need actionable feedback, fast. Actions Nurse is 100% open-source under the MIT license with a zero-friction FastAPI + vanilla JS stack. It also ships as a composite GitHub Action that listens for failed workflow runs, collects failed-step logs, writes the job summary, and preserves a markdown report artifact.*
>  
> *We are targeting:*  
> - **Best Use of Gemma 4**: Applying lightweight, open-weight code models to developer productivity workflows.  
> - **Best Open-Source AI**: Zero lock-in, reliable offline fallback, and practical utility for every developer.*
>  
> *Check out the repo on GitHub: `mangeshraut712/actions-nurse`. Thank you!"*
