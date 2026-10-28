# Deploy Runbook: Cloudflare Pages

Landing page ships as static files. The API stays local until Modal credits land. Do the dashboard steps in order. Nothing here needs paid tiers.

## One-time setup (owner, 10 minutes)

1. Sign in at dash.cloudflare.com. Open Workers and Pages. Select Create. Select the Pages tab. Select Upload assets.
2. Name the project `settleye`. Upload the `frontend/dist` folder from a clean local build.
3. Open the project. Open Custom domains. Add `settleye.com` plus `www.settleye.com`. Approve the DNS prompts.
4. For auto-deploys later: open the project. Open Settings. Open Builds. Connect the `8-BitRhyon/settleye` repo. Set root directory to `frontend`. Set build command to `npm run build`. Set output directory to `dist`.

## CLI alternative (same result)

Run `wrangler login` once in an interactive terminal. Then from the repo root:

```bash
cd frontend && npm run build
wrangler pages project create settleye
wrangler pages deploy ./dist --project-name settleye --branch main
```

## Rebuild checklist before every deploy

1. Run `npm run test` in `frontend`. All 21 checks must pass.
2. Run `npm run typecheck` in `frontend`. Output must be clean.
3. Run `npm run build` in `frontend`. Confirm `dist/landing.html` exists.
4. Deploy the `dist` folder only. Never upload `.env` or `node_modules`.

## What Pages does not host

Pages serves static files only. The FastAPI backend (inbox audit, explain, remediate) cannot run here. Demo options stay: local run (documented in README, under five minutes) plus the recorded video. When Modal credits land, the API deploys there and the landing points at it. Do not rewrite the backend for Workers. That migration buys nothing before judging.
