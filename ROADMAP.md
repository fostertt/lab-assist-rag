# ROADMAP - Lab Assistant RAG

**Last Updated:** 2025-12-26
**Project Status:** Active Development
**Current Phase:** Phase 2: Accessibility & Capability Expansion

---

## 🎯 Project Vision

To create a friction-less, voice-or-text activated AI sysadmin that knows the specific context of the Foster home lab. It should be able to diagnose common issues instantly, take simple corrective actions (like restarting containers), and maintain its own troubleshooting logs, significantly reducing the cognitive load of managing homelab infrastructure.

---

## 📍 Current Position

**Where We Are Now:**
We have a functional "Phase 1" agent. It has "eyes" (RAG that reads local docs accurately) and basic "hands" (ping and logging tools). It is stable and does not hallucinate tool results.

**What's Working Well:**

- "Sniper Mode" RAG is highly effective at finding the right data (IPs, preferences).
- The logging tool correctly persists data to the infrastructure log.

**What Needs Improvement:**

- **Accessibility:** Launching the tool via full terminal paths is cumbersome. It needs to be instantly accessible (alias/Stream Deck).
- **Vision Depth:** It can see if a server is pingable, but doesn't know if the apps _on_ the server (like Plex or Pi-hole containers) are actually running.

---

## 🚀 Active Work (Next Steps)

**Primary Focus:** Making the bot easier to launch and giving it tools to see Docker containers.

### In Progress / Next Up

- [ ] **Quick Launch Alias** (Priority: High)

  - **Notes:** Create a `.bash_aliases` entry so typing `lab` launches the bot instantly.

- [ ] **Docker Awareness Tool** (Priority: High)

  - **Notes:** Add a Python tool that runs `docker ps --format ...` so the bot can list running containers and check their status.

- [ ] **Stream Deck Integration** (Priority: Medium)
  - **Notes:** Create a script that the Stream Deck can trigger to open an SSH window directly into the running bot.

---

## 🗓️ Phase Planning

### Phase 1: Foundation & "Safe Hands" ✅ COMPLETE

**Goal:** Establish the RAG engine and basic, safe interaction tools.
**Key Achievements:**

- Integrated Ollama (Llama 3.1) with LangChain.
- Developed "Sniper Mode" for accurate document retrieval.
- Implemented multi-tool execution engine (Ping, System Check, Log).
- Created core documentation structure (Network Map, Preferences, Logs).

### Phase 2: Accessibility & Capability Expansion 🚧 IN PROGRESS

**Goal:** Remove friction in using the tool and expand its diagnostic capabilities beyond simple networking.
**Planned Work:**

- [X] Shell Alias (`lab`).
- [ ] Docker Tools (list, restart container).
- [ ] Web Service Check Tool (`curl` check for HTTP 200 OK).
- [ ] Stream Deck Launch Button.

### Phase 3: Proactive & Advanced Diagnostics 💡 FUTURE

**Goal:** The bot moves from purely reactive to semi-proactive assistance.
**Ideas:**

- Ability to read the tail of a specific container log upon request.
- A "morning check" script that runs a sequence of tools and logs a health report automatically.
