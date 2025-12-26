# AI_NOTES.md - Lab Assistant RAG (Sysadmin Bot)

**Last Updated:** 2025-12-26
**Project Type:** Automation/Infrastructure/AI Agent
**Primary AI Tool:** Ollama (Llama 3.1 8b local)
**Status:** Active

---

## 📝 Session Log (Reverse Chronological)

### Session 1 (Dec 26, 2025)
- **Completed:**
  - Established `read_docs.py` with RAG "Sniper Mode" logic.
  - Implemented multi-tool execution (Ping, System Check, Logging).
  - Created `lab` shell alias for global quick-launch.
  - Restructured project files into `~/projects/_context`.
- **Next:**
  - Create Docker management tool (`docker ps`, `restart`).
  - Set up Stream Deck SSH launch button.
- **Blockers:** None.

*(Future AI: Add new session notes above this line. Do not overwrite history.)*

---

## 📋 Quick Context

This project is a Python-based command-line AI agent designed to act as a "Junior Sysadmin" for the Foster home lab. It uses RAG (Retrieval-Augmented Generation) to read local documentation (network maps, cheat sheets in `~/projects/_context`) to understand the environment. It has "safe hands," meaning it can execute specific, pre-defined Python functions as tools (currently: `ping`, `check_server`, and `log_note`) based on its understanding of the user's request.

---

## 🛠️ Tech Stack

- **Language:** Python 3.x
- **Core Library:** LangChain (for Ollama integration)
- **AI Model:** Ollama hosting Llama 3.1 (8B) locally
- **Key Dependencies:** `langchain-ollama`, standard Python libraries (`os`, `sys`, `re`, `subprocess`).

---

## 🔐 Key Decisions (Do Not Break Without Asking)

### Decision 1: Local-First Architecture

**Made:** 2025-12-24
**Reasoning:** The bot must run entirely on the local server ("Foster-Server") using Ollama. It should not rely on external APIs (like OpenAI) to ensure privacy, zero latency, and functionality even during internet outages.

### Decision 2: Defined Tool "Safe Hands"

**Made:** 2025-12-25
**Reasoning:** The AI is NOT allowed arbitrary shell execution access. It must interact with the system _only_ through Python functions explicitly defined in the `AVAILABLE_TOOLS` registry in `read_docs.py`. This prevents accidental destructive commands (like `rm -rf`).

### Decision 3: "Sniper Mode" RAG over Vector DB

**Made:** 2025-12-25
**Reasoning:** Instead of a complex vector database, we use a hardcoded `PRIORITY_RULES` dictionary to map keywords (e.g., "ip", "log") to specific markdown files. This ensures 100% accuracy for critical lookups (like finding the network map) before falling back to general keyword matching.

---

## 📊 Current State

**Status:** Active Development
**Working?** Yes.

**What's Working:**

- **RAG context injection:** It successfully reads files from `~/projects/_context` based on keywords.
- **Sniper Mode:** It prioritizes the correct files (e.g., reads `preferences.md` when asked about style).
- **Multi-Tool Execution:** It can correctly identify and execute multiple tools in one prompt (e.g., pinging two different IPs).
- **Logging:** The `log` tool successfully appends notes to the `troubleshooting_log.md`.

**What's Not Working / Known Issues:**

- [ ] It currently only knows about network connectivity (ping). It needs tools to understand application states (Docker containers, web services).
- [ ] Launching it requires typing the full path to the venv python executable. Needs a quick alias.

**Next Actions (Prioritized):**

1. [ ] Create a shell alias (`lab`) for quick launching.
2. [ ] Add a Docker tool (`docker ps`, `docker restart <container>`).
3. [ ] Set up Stream Deck integration for one-touch SSH launch.

---

## ⚡ Common Commands

### Development

```bash
# Activate venv and run the bot
cd ~/projects/lab-assist-rag
source venv/bin/activate
python read_docs.py
```
