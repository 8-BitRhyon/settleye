# AGENTS.md

Operating contract for agents working in this repository. Read before writing.

## Purpose

Settleye is an execution auditor for AI support agents: it extracts promised actions from transcripts and reconciles them against Stripe/Shopify ledger state. Built for the Meta Global AI Developer Hackathon (Indie track, Oct-Nov 2026).

## Stack

- Backend: Python 3.12 + FastAPI (package manager: `uv`, test runner: `pytest`)
- Frontend: Vite + React + TypeScript + Tailwind CSS (`npm`, `vitest`/`tsc`)
- Deploy target: Modal serverless (backend cron + API), static frontend
- Model: `meta-models/muse-spark-open-1026` via Baseten (OpenAI-compatible, event-instructed ID). `MODEL_ID` env overrides. Never hardcode a different ID.

## Commands

- Backend install: `cd backend && uv sync`
- Backend test: `cd backend && uv run pytest`
- Backend dev: `cd backend && uv run uvicorn app.main:app --reload`
- Daemon sweep: `cd backend && uv run python -m app.daemon --dir <transcripts> --ledger mock|shopify` (audit-only). `--auto-remediate` runs on mock only.
- Frontend install: `cd frontend && npm install`
- Frontend test: `cd frontend && npm test`
- Frontend test/typecheck: `cd frontend && npm run typecheck`
- Frontend build: `cd frontend && npm run build`
- Frontend dev: `cd frontend && npm run dev`

## Standards

- **Evidence over hope.** Every change ends with verification: tests, lint, typecheck, or runtime observation. "Seems right" is not done.
- **Read before you write.** Never edit a file you have not read. Never guess names or signatures.
- **One logical change per commit.** Small diffs that can be bisected. No drive-by refactoring.
- **Test first.** New behavior starts as a failing test (red), then implementation (green), then refactor.
- **No em dashes (U+2014).** Use `-` or `:` in every artifact this repo produces.
- **No machine-specific paths.** Never commit absolute home paths. Use `~`, `$HOME`, or relative paths.
- **Secure by default.** Never commit secrets, keys, tokens, or IDs. `.env` stays local. Only `.env.example` is committed. Run the secret scan before pushing.
- **No mock in production paths.** Mocks and fixtures live in `fixtures/` and `tests/` only, behind explicit interfaces. Demo fallback must be labeled as such in the UI.

## Conventions

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`.
- Branch names: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`.
- Signed commits required (`commit.gpgsign=true`).
- This file is the single owner of agent rules. When a fact recurs, update this file. Prefer pruning over appending.
