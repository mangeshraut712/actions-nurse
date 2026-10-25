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

**Action 2**: Click the `npm-typecheck.txt` fixture button.
> *"Let's test an everyday team headache: someone merged a PR with mismatched TypeScript exports. I click `npm-typecheck.txt`, which loads a real CI failure, and click **Triage with Gemma 4**."*  
> *(Show results on screen)*  
> *"Instantly, Actions Nurse isolates:*  
> - *Failing Step: `Typecheck / tsc`*  
> - *Root Cause: Module missing exported members after a merge*  
> - *Suggested Fix: Align exports or rebase onto main*  
> - *Confidence: High."*

**Action 3**: Click `oom-killed.txt`.
> *"Now let's try an infrastructure error: Node.js running out of heap memory during bundling (`Exit Code 134`).*  
> *(Click Triage)*  
> *"Actions Nurse immediately spots the OOM kill and offers the exact environment fix: increasing `NODE_OPTIONS=--max-old-space-size=4096` in the GitHub Actions workflow YAML."*

---

### [1:30 – 2:15] Gemma 4 & Offline Reliability

> *"Under the hood, Actions Nurse utilizes a dual-engine architecture:*  
> 1. *When connected with `GEMINI_API_KEY`, it calls Google's **Gemma 4** (`gemma-4-26b-a4b-it`) via the Gemini API for semantic code reasoning and multimodal screenshot triage.*  
> 2. *Crucially, if you are offline, at a venue with spotty Wi-Fi, or without an API key, our deterministic pattern engine steps in automatically. Your triage and demos never break."*

---

### [2:15 – 2:45] Open Source & Prize Targets

> *"Why this matters for Cloud Native Pune:*  
> *In Kubernetes and CI/CD pipelines, engineers need actionable feedback, fast. Actions Nurse is 100% open-source under the MIT license with a zero-friction FastAPI + vanilla JS stack.*  
>  
> *We are targeting:*  
> - **Best Use of Gemma 4**: Applying lightweight, open-weight code models to developer productivity workflows.  
> - **Best Open-Source AI Project**: Zero lock-in, reliable offline fallback, and practical utility for every developer.*  
>  
> *Check out the repo on GitHub: `mangeshraut712/actions-nurse`. Thank you!"*
