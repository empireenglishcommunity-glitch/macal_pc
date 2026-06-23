# MACAL Agent — Strategic Evolution Blueprint

## Document Type: Planning & Architecture (No Implementation)
## Date: June 23, 2026
## Status: AWAITING APPROVAL — No development begins until explicitly approved

---

## 1. Current System Assessment

### 1.1 What Exists Today

| Component | Status | Capability |
|-----------|:------:|------------|
| Local LLM (Ollama + Qwen3-4B) | Running | Understands instructions, selects tools, generates parameters |
| Agent Daemon (FastAPI, port 8900) | Running | Receives tasks via HTTP, plans + executes |
| File Operations | Working | create_folder, move_file, rename_file, copy_file, write_file, list_directory |
| GUI Operations | Working | open_application, type_text, press_keys, list_windows, focus_window |
| Permission Guard | Working | Action classification (green/yellow/red/black), path validation, rate limiting |
| AI File Organizer | Working | Classifies files by content/extension, moves to organized structure, undo support |
| Telegram Remote Control | Working | Send commands from phone → n8n → agent → executes → replies |
| Tailscale Mesh VPN | Configured | Encrypted PC ↔ Hetzner connection (needs clean network to reconnect) |
| n8n Orchestration | Running | Workflow automation, webhook reception, scheduling |
| Auto-Start on Boot | Configured | Windows Task Scheduler launches agent on login |
| Transaction Logging | Working | Every file operation logged with timestamp for rollback |

### 1.2 Current Architecture

```
TRIGGER LAYER:    Telegram | curl | n8n cron | n8n webhook
                           ↓
ORCHESTRATION:    Hetzner n8n (routes, schedules, notifies)
                           ↓  Tailscale
INTELLIGENCE:     Ollama Qwen3-4B (plans tool calls)
                           ↓
SECURITY:         Permission Guard (validates every action)
                           ↓
EXECUTION:        File Ops | GUI Ops | Shell
                           ↓
PERSISTENCE:      SQLite transaction log | file system
```

### 1.3 Hardware Constraints

| Resource | Available | Constraint Impact |
|----------|-----------|-------------------|
| RAM | 8 GB | Limits model to 4B parameters; can't run multiple models |
| GPU | Intel Iris Xe (integrated) | CPU-only inference; 10-15 tok/s; ~60s planning time |
| Disk | 58 GB free | Adequate for models + data |
| CPU | Modern x86_64 | Adequate for all non-LLM tasks |
| Network | Variable (Fortinet blocks on some networks) | Tailscale/n8n dependent on clean network |

---

## 2. Strengths, Weaknesses, Limitations & Bottlenecks

### 2.1 Strengths

| Strength | Why It Matters |
|----------|---------------|
| Fully self-hosted | Zero vendor dependency, total privacy, $0/month |
| Working end-to-end pipeline | Proven: instruction → plan → execute → result |
| Security-first design | Permission guard, path allowlists, action classification |
| Rollback capability | Every operation reversible |
| Remote triggerable | Telegram → agent from anywhere |
| Modular architecture | Easy to add new tools without changing core |
| Auto-starts on boot | Always ready |

### 2.2 Weaknesses

| Weakness | Impact | Root Cause |
|----------|--------|-----------|
| Slow planning (~60-90s) | Poor UX for interactive use | CPU-only inference on 8GB RAM |
| Single-step intelligence | Can't chain complex multi-step workflows reliably | 4B model has limited multi-step planning |
| No memory/context | Agent forgets everything between tasks | No persistent memory system |
| No file content reading | Can't search inside documents | Only classifies by name/extension |
| No web access | Can't browse, research, or fetch data | No web tools implemented |
| No email integration | Can't read/send/manage email | No email tools |
| No calendar awareness | Doesn't know dates, deadlines, schedules | No calendar integration |
| Telegram reply fragile | Complex formatting breaks Telegram API | Minimal error handling on reply |
| Network dependency | Fortinet/corporate networks break Tailscale | Architecture requires clean network for remote |

### 2.3 Critical Bottlenecks

| Bottleneck | Effect | Priority to Fix |
|-----------|--------|:---------------:|
| **LLM speed (60-90s per task)** | Makes interactive use painful | HIGH |
| **No persistent memory** | Agent can't learn, remember preferences, or build context | HIGH |
| **Single-tool execution** | Most real tasks need 3-10 steps; agent often picks only 1 | HIGH |
| **No content reading** | Can't search inside PDFs, docs, or text files | MEDIUM |
| **No internet access** | Can't research, check prices, get updates | MEDIUM |

---

## 3. Phased Roadmap

---

### PHASE A: Immediate High-Impact Improvements

**Timeline:** 1-2 weeks | **Theme:** Fix bottlenecks, make the agent actually useful daily

---

#### A1. Speed Optimization — Reduce Planning Time from 60s to 10-15s

**Why it matters:** 60-second wait makes the agent painful to use. If it responds in 10-15 seconds, it becomes a tool you actually reach for.

**Expected impact:** 4-6x faster response time
**Complexity:** Medium
**Dependencies:** None

**Approach:**
- Use a **smaller model for simple routing** (Qwen3-0.8B for "which tool?" → Qwen3-4B only for complex planning)
- **Cache common tool selections** (if instruction contains "create folder" → always `create_folder`, skip LLM)
- **Reduce token count**: strip tool descriptions for obvious matches; send fewer tools per call
- **Pre-warm the model**: keep Qwen3-4B loaded in RAM (Ollama already does this if recently used)
- **Template matching**: for 10-20 most common instructions, bypass LLM entirely with regex patterns

**Priority:** ★★★★★ (Highest — everything else feels slow without this)

---

#### A2. Persistent Memory System

**Why it matters:** Without memory, the agent is amnesia-level useless for complex work. It can't remember your preferences, project structures, naming conventions, or context.

**Expected impact:** Agent becomes contextually intelligent; knows YOUR system
**Complexity:** Medium
**Dependencies:** SQLite (already have), embedding model (optional)

**Approach:**
- **Fact Store** (SQLite): user preferences, project paths, naming rules, frequently used locations
- **Task History**: searchable log of past tasks + results (what worked, what failed)
- **Context Injection**: before each LLM call, inject relevant memory (last 5 tasks, user prefs, current project)
- **Learning Loop**: when user corrects the agent ("no, put it in Documents not Desktop"), store the correction as a rule

**Examples of remembered context:**
- "User prefers Documents/Work/ for business files"
- "User's real estate files go in Documents/Real-Estate/{project-name}/"
- "User's naming convention: YYYY-MM-DD_description.ext"
- "Last 3 tasks were about the Jade Tower project"

**Priority:** ★★★★★ (Transforms agent from tool into assistant)

---

#### A3. Multi-Step Execution (Task Chaining)

**Why it matters:** Most real tasks require 3-10 steps. Currently the agent often picks only 1 tool per instruction.

**Expected impact:** Agent handles complex instructions like "create a project folder with subfolders, add a README, and open it in Explorer"
**Complexity:** Medium
**Dependencies:** A1 (speed) makes this practical

**Approach:**
- **ReAct loop**: plan → execute step 1 → observe result → plan next step → repeat
- **Structured planning prompt**: force LLM to output an ordered list of steps BEFORE executing
- **Step verification**: after each step, confirm success before proceeding
- **Rollback on failure**: if step 3 fails, undo steps 1-2

**Priority:** ★★★★☆

---

#### A4. File Content Reading

**Why it matters:** An agent that can only see filenames is half-blind. Reading file contents enables: search, summarization, intelligent classification, data extraction.

**Expected impact:** Agent can answer "find the contract with Company X" or "summarize this PDF"
**Complexity:** Low (libraries already installed: pymupdf, python-docx, openpyxl)
**Dependencies:** None

**Tools to add:**
- `read_file_content` — read text from .txt, .md, .py, .json, .csv
- `read_pdf_text` — extract text from PDF
- `read_docx_text` — extract text from Word docs
- `read_excel_data` — read spreadsheet contents
- `search_files_by_content` — grep across multiple files

**Priority:** ★★★★☆

---

#### A5. Improved Telegram Integration

**Why it matters:** Telegram is your primary remote interface. Currently replies are minimal ("completed - instruction"). Need rich, informative responses.

**Expected impact:** Usable mobile-first interface
**Complexity:** Low
**Dependencies:** n8n workflow update (when network is available)

**Improvements:**
- Detailed results with file paths and counts
- Error messages that are actually helpful
- `/organize` command — triggers file organizer
- `/undo` command — reverses last operation
- `/list` command — show recent tasks
- Progress updates for long-running tasks
- Photo/file sending capability (agent can send you a file via Telegram)

**Priority:** ★★★★☆

---

### PHASE B: Short-Term Enhancements

**Timeline:** 2-4 weeks | **Theme:** Expand capabilities into daily workflows

---

#### B1. Web Research & Browsing

**Why it matters:** Most knowledge work requires internet access — checking prices, researching properties, reading articles, verifying information.

**Expected impact:** Agent becomes a research assistant
**Complexity:** Medium
**Dependencies:** Playwright MCP (already in requirements)

**Capabilities:**
- `web_search` — search Google/DuckDuckGo, return top results
- `web_fetch` — fetch and extract text from a URL
- `web_screenshot` — capture a webpage screenshot
- Open URLs in browser on command

**Use cases:**
- "Search for Jade Tower Dubai current prices"
- "Get me the latest RERA regulations PDF"
- "What's the USD/AED exchange rate today?"

**Priority:** ★★★★☆

---

#### B2. Email Management (Gmail/Outlook)

**Why it matters:** Email is central to business. Auto-classify, summarize, draft replies, extract attachments.

**Expected impact:** Save 30-60 min/day on email management
**Complexity:** High (OAuth setup, API integration)
**Dependencies:** Web access (B1), content reading (A4)

**Capabilities:**
- Read unread emails, summarize top 10
- Search emails by sender/subject/content
- Draft reply based on context
- Extract and save attachments to organized folders
- Flag/archive based on rules

**Priority:** ★★★☆☆

---

#### B3. Document Generation & Templates

**Why it matters:** Real estate, business, and education all require generating documents — proposals, reports, summaries, certificates.

**Expected impact:** Agent produces professional documents from natural language
**Complexity:** Medium
**Dependencies:** A4 (file content reading), write_file (already done)

**Capabilities:**
- Generate markdown reports from data
- Fill document templates with variables
- Create PDF from markdown (via pandoc or weasyprint)
- Generate structured data files (CSV, JSON)
- Create project scaffolds (folder structure + boilerplate files)

**Use cases:**
- "Create a property investment report for Jade Tower unit 1603"
- "Generate a student progress report template"
- "Create a marketing content calendar for next month"

**Priority:** ★★★☆☆

---

#### B4. Scheduled Automations (Cron Jobs via n8n)

**Why it matters:** The most powerful automations are ones that run without you asking.

**Expected impact:** PC maintains itself; daily organization, reports, cleanups
**Complexity:** Low (n8n already supports this)
**Dependencies:** Network access to n8n

**Automations to schedule:**
- **Daily 2 AM**: Organize new Downloads folder files
- **Daily 9 AM**: Send Telegram summary of yesterday's agent activity
- **Weekly**: Disk space check + cleanup recommendations
- **Weekly**: Backup agent configuration and memory
- **On demand**: Full system health report

**Priority:** ★★★☆☆

---

#### B5. Clipboard & Quick Capture

**Why it matters:** You often copy text, links, or data that should be saved somewhere. Agent could watch clipboard and intelligently file snippets.

**Expected impact:** Never lose copied information
**Complexity:** Low
**Dependencies:** None

**Capabilities:**
- Watch clipboard for URLs → auto-bookmark
- Watch for copied text → save to daily notes file
- "Save this to my research" — append clipboard to a designated file
- Quick capture: hotkey → agent saves whatever is in clipboard with context

**Priority:** ★★★☆☆

---

### PHASE C: Medium-Term Expansion

**Timeline:** 1-2 months | **Theme:** Domain-specific intelligence

---

#### C1. Real Estate Assistant Module

**Why it matters:** You work in real estate. A specialized module would handle property data, ROI calculations, document management, client tracking.

**Expected impact:** Dedicated AI assistant for your core business
**Complexity:** Medium
**Dependencies:** B1 (web), B3 (documents), A4 (content reading)

**Capabilities:**
- Property file organization (by project, unit, document type)
- ROI/yield calculator from natural language
- Auto-extract key data from floor plans, factsheets, contracts
- Client document tracker (passport, EID, contracts — check completeness)
- Market data research and comparison

**Priority:** ★★★★☆ (High personal value)

---

#### C2. Trading & Investment Monitor

**Why it matters:** Stay informed about markets without constant manual checking.

**Expected impact:** Automated market awareness
**Complexity:** Medium
**Dependencies:** B1 (web), scheduled automations (B4)

**Capabilities:**
- Fetch crypto/stock/forex prices on demand
- Daily/weekly portfolio summary
- Price alert system (notify via Telegram when thresholds hit)
- News aggregation for tracked assets
- Simple technical analysis (moving averages, RSI)

**Priority:** ★★★☆☆

---

#### C3. Content Creation Engine

**Why it matters:** You manage Empire English Community — need regular content for LinkedIn, Telegram, social media.

**Expected impact:** Content pipeline semi-automated
**Complexity:** Medium
**Dependencies:** Memory (A2), web (B1), document generation (B3)

**Capabilities:**
- Generate LinkedIn posts in your brand voice (you already have a brand bible)
- Create educational content for English learners
- Schedule content via n8n → social media APIs
- Repurpose long content into short-form (thread → carousel → caption)
- Research trending topics in English education niche

**Priority:** ★★★☆☆

---

#### C4. Knowledge Base & Research System

**Why it matters:** You accumulate documents, PDFs, research. Finding information across hundreds of files is impossible manually.

**Expected impact:** Ask questions → get answers from YOUR documents
**Complexity:** High (requires RAG — Retrieval Augmented Generation)
**Dependencies:** A4 (content reading), embedding model (small, can run locally)

**Capabilities:**
- Index all documents in ~/Organized/ (extract text, create embeddings)
- Natural language search: "What was the price per sqft in the Jade Tower contract?"
- Summarize multiple documents into one brief
- Compare documents (find differences between two contracts)
- Auto-tag and cross-reference related documents

**Priority:** ★★★☆☆

---

#### C5. Multi-Device Coordination

**Why it matters:** You have a PC + phone + potentially a laptop. Agent should coordinate across devices.

**Expected impact:** Seamless experience regardless of which device you're on
**Complexity:** Medium
**Dependencies:** Tailscale (already set up), n8n

**Capabilities:**
- Send files from PC to phone (via Telegram)
- Trigger PC actions from phone
- Sync clipboard between devices
- "Send this file to my phone" → agent uploads via Telegram bot
- Remote file browser via Telegram

**Priority:** ★★☆☆☆

---

### PHASE D: Advanced Capabilities

**Timeline:** 2-4 months | **Theme:** Autonomous intelligence

---

#### D1. Learning & Self-Improvement System

**Why it matters:** Every correction you make should make the agent better permanently.

**Expected impact:** Agent gets smarter over time without any code changes
**Complexity:** High
**Dependencies:** A2 (memory system)

**Approach:**
- Track success/failure rates per tool, per instruction type
- When user says "wrong" → store correction as a rule
- Periodic self-evaluation: "which tasks do I fail most?"
- Suggest optimizations: "I notice you always organize Downloads at 10 PM — should I do it automatically?"

**Priority:** ★★★☆☆

---

#### D2. Multi-Agent Collaboration

**Why it matters:** Different tasks need different expertise. A "research agent" thinks differently than a "file manager agent."

**Expected impact:** Specialized agents that are better at their specific domain
**Complexity:** High
**Dependencies:** Speed optimization (A1), memory (A2)

**Approach:**
- Router agent (fast, small model) decides which specialist to invoke
- File Agent (knows your folder structure)
- Research Agent (knows how to search and summarize)
- Business Agent (knows real estate terminology, calculations)
- Creative Agent (knows your brand voice, content style)

**Priority:** ★★☆☆☆

---

#### D3. Voice Control

**Why it matters:** Hands-free operation — speak commands instead of typing.

**Expected impact:** Agent accessible without keyboard
**Complexity:** Medium
**Dependencies:** Whisper.cpp (free, local speech-to-text)

**Flow:** Speak → Whisper converts to text → Agent processes → Responds via TTS or Telegram

**Priority:** ★★☆☆☆

---

#### D4. Proactive Agent (Suggestions & Alerts)

**Why it matters:** Instead of waiting for commands, the agent notices things and suggests actions.

**Expected impact:** Agent becomes a proactive assistant, not just reactive
**Complexity:** High
**Dependencies:** Memory (A2), scheduled automations (B4)

**Examples:**
- "You have 15 files in Downloads that haven't been organized in 3 days"
- "Your Documents/Real-Estate/Jade-Tower/ has an unsigned contract from 2 weeks ago"
- "Disk space is getting low — should I clean Docker images?"
- "You haven't backed up your agent configuration in 7 days"

**Priority:** ★★☆☆☆

---

### PHASE E: Long-Term Vision

**Timeline:** 6+ months | **Theme:** Personal Operating System

---

#### E1. MACAL OS — Unified Interface

All interactions through a single, beautiful dashboard:
- Web UI (local) showing agent status, recent tasks, memory, files
- Telegram as mobile interface
- Voice as hands-free interface
- All modules accessible from one place

#### E2. Plugin Marketplace

Architecture where new capabilities can be added as plugins:
- Each plugin = one Python file + tool registration
- Community-contributed plugins
- Domain-specific plugin packs (real estate pack, trading pack, education pack)

#### E3. Full Workflow Automation Platform

Visual workflow builder (like n8n but agent-native):
- "When a new PDF appears in Downloads AND it contains 'invoice' → move to Invoices, extract amount, log to spreadsheet, notify via Telegram"
- Event-driven architecture with triggers, conditions, and actions

#### E4. Team Mode

Multiple users, each with their own permissions:
- Admin (you) has full control
- Employees can trigger specific workflows only
- Clients can interact via their own Telegram bot (limited capabilities)

---

## 4. Priority Matrix

```
                    HIGH IMPACT
                        │
         A1 (Speed) ────┼──── A2 (Memory)
                        │
         A3 (Multi-step)│     C1 (Real Estate)
                        │
    A4 (Content Read) ──┼──── A5 (Telegram)
                        │
         B1 (Web) ──────┼──── B4 (Scheduled)
                        │
         B3 (Documents) │     B2 (Email)
                        │
    ────────────────────┼──────────────────────
    LOW COMPLEXITY      │      HIGH COMPLEXITY
                        │
         B5 (Clipboard) │     C4 (Knowledge Base)
                        │
         C3 (Content) ──┼──── D1 (Learning)
                        │
                   D3 (Voice)  D2 (Multi-Agent)
                        │
                    LOW IMPACT
```

---

## 5. Recommended Execution Order

| Order | Item | Why First |
|:-----:|------|-----------|
| 1 | **A1: Speed Optimization** | Everything feels broken at 60s; fix this first |
| 2 | **A4: File Content Reading** | Low effort, high utility; enables C1, C4, B3 |
| 3 | **A2: Persistent Memory** | Transforms agent from tool to intelligent assistant |
| 4 | **A3: Multi-Step Execution** | Makes the agent actually capable of complex tasks |
| 5 | **A5: Telegram Improvements** | Better mobile experience; already partially done |
| 6 | **B1: Web Research** | Opens up information access |
| 7 | **B4: Scheduled Automations** | Set-and-forget productivity |
| 8 | **C1: Real Estate Module** | Direct business value |
| 9 | **B3: Document Generation** | Produces tangible output |
| 10 | **C2: Trading Monitor** | Passive information value |

---

## 6. Architecture Evolution

### Current (v0.2)
```
Single LLM → Single Tool Call → Single Execution → Done
```

### Target (v1.0)
```
Instruction → Router (fast, cached) → Specialist Model
    → Multi-Step Planner → Permission Check (per step)
    → Execute Step 1 → Verify → Execute Step 2 → ...
    → Store Results in Memory → Notify User → Log
```

### Target (v2.0)
```
TRIGGERS (scheduled, webhook, file change, proactive)
    → Router → Agent Selection → Context Injection (memory + relevant docs)
    → Planning (with self-critique) → Execution (with rollback)
    → Learning (store outcomes) → Notification (multi-channel)
```

---

## 7. Performance Optimization Strategy

| Technique | Current → Target | How |
|-----------|:----------------:|-----|
| **Regex routing** | 60s → 0.1s for common tasks | Pattern match "create folder X" → skip LLM entirely |
| **Two-tier model** | 60s → 15s for complex tasks | 0.8B routes, 4B only for ambiguous cases |
| **Tool subset selection** | 14 tools per call → 3-5 relevant | Reduce prompt size = faster inference |
| **Response caching** | Full LLM call every time → cached for repeats | Same instruction = same plan |
| **Async execution** | Wait for LLM → execute → wait → reply | Execute immediately for cached patterns |

---

## 8. Security & Safety Enhancements

| Enhancement | Why | Priority |
|-------------|-----|:--------:|
| **API key authentication** on agent endpoint | Currently no auth — anyone on Tailscale can call it | HIGH |
| **Confirmation for bulk operations** (>10 files) | Prevent AI from mass-moving files incorrectly | HIGH |
| **Daily audit email** | Know what the agent did while you weren't watching | MEDIUM |
| **Network isolation** | Agent process can't reach internet unless explicitly asked | MEDIUM |
| **Encrypted memory store** | Protect stored preferences and context | LOW |

---

## 9. Cost Analysis

| Phase | Hardware Need | Software Cost | Time Investment |
|-------|:------------:|:-------------:|:--------------:|
| A (Immediate) | None — use existing | $0 | 1-2 weeks |
| B (Short-term) | None | $0 | 2-4 weeks |
| C (Medium-term) | 16GB RAM recommended | $30-50 one-time (RAM stick) | 1-2 months |
| D (Advanced) | 16GB RAM + optional GPU | $0-150 one-time | 2-4 months |
| E (Long-term) | Optional better hardware | $0 | 6+ months |

**All phases achievable at $0 monthly recurring cost.**
16GB RAM upgrade ($30-50 one-time) is the single highest-ROI hardware investment — enables Qwen3-8B which is dramatically better at multi-step reasoning and tool use.

---

## 10. Key Metrics to Track

| Metric | Current | Target (v1.0) |
|--------|:-------:|:-------------:|
| Avg response time | 60-90s | <15s |
| Task success rate | ~80% | >95% |
| Tasks per day (automated) | 0 | 10-50 |
| Human interventions needed | Every task | <10% of tasks |
| Tools available | 14 | 40+ |
| Domains covered | Files + GUI | Files, Web, Email, Documents, Research |
| Memory entries | 0 | 500+ |
| Scheduled automations | 0 | 5-10 daily |

---

## 11. Decision Points Requiring Your Input

Before implementation, I need your decisions on:

1. **RAM upgrade**: Are you willing to buy a 16GB stick (~$30-50)? This would enable Qwen3-8B which is significantly better at complex tasks.

2. **Priority domain**: Which matters most for your daily work — real estate, trading, content creation, or general productivity?

3. **Speed vs capability trade-off**: Would you prefer faster responses (smaller model, simpler logic) or more capable responses (larger model, slower)?

4. **Privacy level**: Are you comfortable with the agent reading all your documents for the knowledge base? Or do you want certain folders excluded?

5. **Automation comfort**: How much should the agent do without asking? (Staging mode vs auto-execute for scheduled tasks)

---

*This blueprint is a PLAN ONLY. No implementation begins until you review and approve. Tell me which phases or items to prioritize, and we execute together.*
