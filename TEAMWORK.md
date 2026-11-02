# TEAMWORK: Tooling and Impact Push (Nov 1-3, 2026)

## User

Primary user for this push: the hackathon judge. Proxy buyer for the written story: support ops lead at a merchant running 5,000 to 50,000 tickets a month with an AI agent handling refunds. The judge decides in days. The ops lead decides in weeks. Copy speaks to the ops lead, proof is built for the judge.

## Job

Prove each flagged drift is real with citable evidence. Detection is already strong. Evidence is the gap that keeps Impact and Technical depth from scoring higher.

## Constraints

- Model spend for this push: $10 or less.
- No feature that cannot appear in a 3-minute video.
- Lighthouse floor 85. Accessibility 100.
- Every number on the public page traces to a committed file.
- Freeze starts Nov 3, 18:00. After that, distribution only.

## Acceptance criteria and independent checks

1. A judge reaches a rendered drift from the public link in 60 seconds or less, with no install.
   Check: fresh browser profile, public URL, stopwatch. Record the seconds.
2. Every claim on the landing page maps to a committed evidence file.
   Check: claim list against files in `docs/research/` and `README.md`. Any claim without a file is cut or qualified.
3. The live API path works end to end from a clean clone.
   Check: clone to new directory, follow README verbatim, audit the sample transcript, see a drift.
4. Impact narrative carries one merchant-facing number per buyer tier.
   Check: copy audit against the tier table. SMB, mid-market, enterprise each get one number.

## File ownership (no two writers on one file)

- `frontend/landing.html`, `frontend/src/App.tsx`, `frontend/src/sample.ts`: one worker only.
- `docs/research/*`: evidence index worker only.
- `README.md`: integrator only.
- Backend: read only for this push. No changes unless a check fails.

## Scout tracks (Phase 2)

Each returns finding, evidence, implication, one bet.

1. User: what the judge actually needs to see in 60 seconds.
2. Market: which Impact number survives a skeptical judge.
3. Technical: smallest change that makes evidence verifiable on the public page.
4. Design: how evidence reads visually without clutter.
5. Distribution: what makes judges click and share.
6. Risk: what could make this look fake or fragile.
7. Alpha: the one wedge that beats the field, chosen blind.

## Sequence

Phase 2 fans out scouts. Phase 3 judges competing theses blind. Phase 4 assigns disjoint files. Phase 5 verifies against the four criteria above, not unit tests alone.
