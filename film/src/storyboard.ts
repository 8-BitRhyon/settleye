/**
 * Storyboard as TypeScript data. Locked to docs/demo-script.md (3:00).
 *
 * Rule: every spoken or on-screen claim in this file already exists in
 * docs/demo-script.md. No new numbers, no new product claims. Captured
 * beats use real screenshots and real API receipts from capture/, never
 * recreated app UI.
 */

export interface Cue {
  /** Seconds from scene start. */
  at: number;
  /** Seconds the cue stays fully on screen. */
  hold: number;
  kind: "kicker" | "line" | "big" | "money" | "caption" | "card" | "image" | "receipt";
  text: string;
  sub?: string;
  /** For kind=image: file under capture/. */
  image?: string;
  tone?: "ink" | "pine" | "alarm" | "gold";
}

export interface Scene {
  id: string;
  /** Beat label from docs/demo-script.md. */
  beat: string;
  start: number;
  duration: number;
  /** Verbatim voiceover slot for this beat (human VO is laid over later). */
  vo: string;
  mode: "code" | "capture";
  cues: Cue[];
}

export const WIDTH = 1920;
export const HEIGHT = 1080;
export const FPS = 24;
export const DURATION = 180;

export const MODEL_ID = "meta-models/muse-spark-open-1026";
export const REPO_URL = "github.com/8-BitRhyon/settleye";

export const storyboard: Scene[] = [
  {
    id: "hook",
    beat: "0:00-0:20 The hook (Impact)",
    start: 0,
    duration: 20,
    mode: "code",
    vo: "Every AI support agent, yours, mine, Grok, Atlas, any of them, will eventually tell a customer 'your refund is processed' when nothing was processed. The agent is not lying. It just never checks. Each phantom refund costs $45, plus a $128 chargeback when the customer gives up waiting. I'm [name], and this is Settleye: the auditor for AI agents.",
    cues: [
      { at: 0.5, hold: 3.2, kind: "kicker", text: "SETTLEYE", sub: "The auditor for AI agents", tone: "pine" },
      { at: 4.0, hold: 4.6, kind: "line", text: "\"Your refund is processed\"", sub: "when nothing was processed", tone: "alarm" },
      { at: 9.0, hold: 3.6, kind: "line", text: "The agent is not lying.", sub: "It just never checks.", tone: "ink" },
      { at: 13.0, hold: 6.2, kind: "money", text: "$45 + $128", sub: "Each phantom refund costs $45, plus a $128 chargeback when the customer gives up waiting.", tone: "alarm" },
    ],
  },
  {
    id: "pain",
    beat: "0:20-0:45 The pain, quantified",
    start: 20,
    duration: 25,
    mode: "code",
    vo: "Air Canada's chatbot invented a refund policy and the tribunal made them honor it. Priceline's bot promised refunds on non-refundable bookings. One phantom refund a week leaks $2,340 a year per merchant, approaching $4,700 once chargebacks land.",
    cues: [
      { at: 0.5, hold: 6.5, kind: "card", text: "Air Canada", sub: "Chatbot invented a refund policy. The tribunal made them honor it.", tone: "alarm" },
      { at: 7.5, hold: 6.5, kind: "card", text: "Priceline", sub: "Bot promised refunds on non-refundable bookings.", tone: "alarm" },
      { at: 14.5, hold: 4.8, kind: "money", text: "$2,340 / year", sub: "One phantom refund a week leaks $2,340 a year per merchant", tone: "gold" },
      { at: 19.8, hold: 4.6, kind: "money", text: "approaching $4,700", sub: "once chargebacks land", tone: "alarm" },
    ],
  },
  {
    id: "extraction",
    beat: "0:45-1:30 The Meta core (Tooling plus Depth)",
    start: 45,
    duration: 45,
    mode: "capture",
    vo: "Watch the middle panel. The Meta model, muse-spark-open, reads the messy dialogue and returns structured promise objects: action, amount, order, system, confidence, and the exact quote. No regex anywhere. The model is the only path from words to promises. Output is Pydantic-validated, repairs itself twice, then fails loudly instead of guessing.",
    cues: [
      { at: 0.3, hold: 9.0, kind: "image", text: "Paste the transcript. Click Audit.", sub: "Real inbox, sample transcript prefilled. Live local stack.", image: "01-inbox.png", tone: "ink" },
      { at: 9.7, hold: 9.0, kind: "image", text: "The Meta model reads the messy dialogue", sub: MODEL_ID + " - No regex anywhere. The model is the only path from words to promises.", image: "02-auditing.png", tone: "pine" },
      { at: 19.1, hold: 13.5, kind: "image", text: "Structured promise objects: action, amount, order, system, confidence, exact quote", sub: "Output is Pydantic-validated, repairs itself twice, then fails loudly instead of guessing. Ledger: $0.00 settled of $45.00 promised.", image: "03-drift.png", tone: "alarm" },
      { at: 33.0, hold: 11.4, kind: "image", text: "Why does this matter?", sub: "The model explains the mismatch in one merchant sentence. Real /explain response, captured live.", image: "04-explain.png", tone: "pine" },
    ],
  },
  {
    id: "fix",
    beat: "1:30-2:15 The fix",
    start: 90,
    duration: 45,
    mode: "capture",
    vo: "One click executes the corrective refund against the test ledger. Receipt carries an idempotency key. Watch me click it again: same key, original receipt, ledger untouched. No double refunds, ever. Card flips to Verified, savings header moves to $45. That is the firewall: promise, proof, patch.",
    cues: [
      { at: 0.3, hold: 8.5, kind: "image", text: "Click \"Issue $45.00 refund.\"", sub: "One click executes the corrective refund against the test ledger.", image: "03-drift.png", tone: "alarm" },
      { at: 9.2, hold: 11.5, kind: "image", text: "Card flips to Verified. Savings header moves to $45.", sub: "Promise, proof, patch.", image: "05-verified.png", tone: "pine" },
      { at: 21.1, hold: 13.5, kind: "receipt", text: "Click it again: same key, original receipt, ledger untouched.", sub: "Real second POST /remediate during capture. Status flips to already_executed. No double refunds, ever.", tone: "pine" },
      { at: 35.0, hold: 9.4, kind: "image", text: "That is the firewall: promise, proof, patch.", sub: "Verified card and recovered total stay put after the re-click.", image: "05-verified.png", tone: "pine" },
    ],
  },
  {
    id: "math",
    beat: "2:15-2:45 The numbers (Impact)",
    start: 135,
    duration: 30,
    mode: "code",
    vo: "This inbox pays for itself the first time it fires in a month. Mid-market math: about $494 of monthly value against a $99 plan, six-day payback. Every $1 of dispute loss costs merchants $4.61 all-in. Our open eval scores 12 of 12 verdicts correct, and no retracted promise ever reported drift. And every save is itemized, not vibes.",
    cues: [
      { at: 0.5, hold: 6.0, kind: "line", text: "Pays for itself the first time it fires in a month", sub: "This inbox", tone: "pine" },
      { at: 7.0, hold: 7.5, kind: "money", text: "$494 vs $99", sub: "About $494 of monthly value against a $99 plan. Six-day payback.", tone: "pine" },
      { at: 15.0, hold: 6.0, kind: "money", text: "$4.61", sub: "Every $1 of dispute loss costs merchants $4.61 all-in.", tone: "gold" },
      { at: 21.5, hold: 8.0, kind: "money", text: "12 of 12", sub: "Open eval: 12 of 12 verdicts correct. No retracted promise ever reported drift. Every save is itemized, not vibes.", tone: "ink" },
    ],
  },
  {
    id: "vision",
    beat: "2:45-3:00 Vision plus compliance (end card on screen)",
    start: 165,
    duration: 15,
    mode: "code",
    vo: "Every payment needs a ledger. Every agent needs an auditor. The nightly sweep already catches orders promised across several tickets. Built [dates] for this event on Meta open weights. Repo link, setup under five minutes, synthetic data only, no live payments.",
    cues: [
      { at: 0.3, hold: 5.2, kind: "line", text: "Every payment needs a ledger.", sub: "Every agent needs an auditor.", tone: "pine" },
      { at: 5.8, hold: 4.2, kind: "line", text: "The nightly sweep already catches orders promised across several tickets", sub: "Built for this event on Meta open weights.", tone: "ink" },
      { at: 10.3, hold: 4.4, kind: "card", text: "SETTLEYE", sub: REPO_URL + "  -  " + MODEL_ID + "\nSetup under five minutes. Synthetic data only, no live payments.\nuv run pytest  plus  npm run build  green.", tone: "pine" },
    ],
  },
];
