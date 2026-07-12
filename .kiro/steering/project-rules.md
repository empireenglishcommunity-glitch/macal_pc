# macal_pc — AI Agent Steering Rules

> This file is automatically loaded by Kiro and any AI agent working on
> this repository.

## Session Protocol

Full session commands (`/start`, `/status`, `/sync`, `/sync dry`,
`/checkpoint`) and standing ecosystem-wide rules live in
`empireenglishcommunity-glitch/Kiro-Master-Index/.kiro/steering/AI-AGENT-PROTOCOL.md`.
Read that file at the start of every session, before anything below.

## Project Identity

- **Project:** MACAL Agent System — an AI desktop agent for Windows 11, controlled via natural language (Telegram/n8n/terminal), powered by local Ollama inference.
- **Parent brand:** MACAL Empire — a **separate side project from Empire English Community**, do not conflate the two when reading `Kiro-Master-Index`.
- **Repository:** `empireenglishcommunity-glitch/macal_pc`
- **Status as of 2026-07-12:** Early stage. Phase 0 (project scaffolding) complete. Phases 1-8 (LLM integration, file operations, GUI automation, security framework, production deployment) scaffolded or planned, not built out. Depends on Ollama + a Windows 11 PC setup outside this repo.

## Repo-Specific Notes

- This is the healthiest-documented repo in the org as of the 2026-07-12 audit — status reporting here has been consistently honest (no claims of completion beyond what's actually built). Keep it that way: update `IMPLEMENTATION_ROADMAP.md`'s phase table accurately as work progresses, don't mark a phase "done" until it's actually verified working, not just scaffolded.
- Security model (GREEN/YELLOW/RED/BLACK action classification, path allowlists, kill switch) is a core design constraint — do not weaken it for convenience when implementing later phases.
