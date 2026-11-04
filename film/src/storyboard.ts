/**
 * Storyboard as TypeScript data. Locked to docs/demo-script.md (3:00).
 *
 * The visual system matches frontend/landing.html: ink, cream, mint, alarm,
 * Fraunces display, Manrope body, JetBrains Mono labels and money.
 * Captured beats use real screenshots and real API receipts from capture/,
 * never recreated app UI. No new numbers beyond the claim ledger.
 */

export interface Fact {
  label: string;
  value: string;
  tone?: "ink" | "pine" | "alarm" | "gold" | "mint" | "cream";
}

export interface Cue {
  /** Seconds from scene start. */
  at: number;
  /** Seconds the cue stays fully on screen. */
  hold: number;
  kind:
    | "kicker"
    | "line"
    | "big"
    | "money"
    | "caption"
    | "card"
    | "image"
    | "receipt"
    | "hero"
    | "end";
  text: string;
  sub?: string;
  /** Optional second hero line. */
  highlight?: string;
  /** Small mono label above the cue. */
  label?: string;
  /** Fact rows for hero, image, or receipt layouts. */
  facts?: Fact[];
  /** For kind=image: file under capture/. */
  image?: string;
  imagePosition?: string;
  imageFit?: "cover" | "contain";
  tone?: "ink" | "pine" | "alarm" | "gold" | "mint" | "cream";
}

export interface Scene {
  id: string;
  /** Beat label from docs/demo-script.md. */
  beat: string;
  start: number;
  duration: number;
  /** Verbatim voiceover slot for this beat. Human VO is laid over later. */
  vo: string;
  mode: "code" | "capture";
  tone: "light" | "dark";
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
    beat: "0:00-0:20 The hook",
    start: 0,
    duration: 20,
    mode: "code",
    tone: "light",
    vo: "Your AI support agent told the customer the refund was processed. The ticket closed. The ledger says zero dollars moved. The agent is not lying. It just never checks. Each phantom refund is forty-five dollars, plus a chargeback. I'm Rhyon, and this is Settleye.",
    cues: [
      {
        at: 0.3,
        hold: 8.7,
        kind: "hero",
        text: "Your refund is processed.",
        highlight: "The ledger says $0.00 moved.",
        sub: "One promise. One ledger. One receipt.",
        facts: [
          { label: "PROMISE", value: "$45.00" },
          { label: "SETTLED", value: "$0.00", tone: "alarm" },
          { label: "STATUS", value: "DRIFT", tone: "alarm" },
        ],
      },
      {
        at: 9.2,
        hold: 4.6,
        kind: "line",
        text: "The agent is not lying.",
        sub: "It just never checks.",
        tone: "ink",
      },
      {
        at: 13.9,
        hold: 5.8,
        kind: "money",
        label: "EACH PHANTOM REFUND",
        text: "$45 + $128",
        sub: "The refund the customer was promised, plus the chargeback when they give up waiting.",
        tone: "alarm",
      },
    ],
  },
  {
    id: "pain",
    beat: "0:20-0:45 The pain, quantified",
    start: 20,
    duration: 25,
    mode: "code",
    tone: "dark",
    vo: "Air Canada's chatbot invented a refund policy. A tribunal made them honor it. Priceline's bot promised refunds on non-refundable bookings. One phantom refund a week leaks two thousand three hundred forty dollars a year. Add chargebacks and it approaches four thousand seven hundred. The industry grades the conversation. The customer waits for the money.",
    cues: [
      {
        at: 0.4,
        hold: 6.2,
        kind: "card",
        label: "PRECEDENT / 01",
        text: "Air Canada",
        sub: "The chatbot invented a refund policy. A tribunal made them honor it.",
        tone: "alarm",
      },
      {
        at: 7.0,
        hold: 6.2,
        kind: "card",
        label: "PRECEDENT / 02",
        text: "Priceline",
        sub: "The bot promised refunds on non-refundable bookings.",
        tone: "alarm",
      },
      {
        at: 13.6,
        hold: 5.4,
        kind: "money",
        label: "ONE A WEEK",
        text: "$2,340 / year",
        sub: "One phantom refund a week leaks $2,340 a year per merchant.",
        tone: "cream",
      },
      {
        at: 19.4,
        hold: 5.2,
        kind: "money",
        label: "WITH CHARGEBACKS",
        text: "$4,700 all-in",
        sub: "The refund, the fee, the labor, and the customer you lose.",
        tone: "alarm",
      },
    ],
  },
  {
    id: "extraction",
    beat: "0:45-1:30 The Meta core",
    start: 45,
    duration: 45,
    mode: "capture",
    tone: "dark",
    vo: "Watch the screen. Muse Spark Open reads the messy dialogue and returns structured promises: action, amount, order, system, confidence, and the exact quote. No regex. The model is the only path from words to promises. Every reply is Pydantic-validated, repaired at most twice, then fails loudly. The model never decides whether money moved. Reconciliation is deterministic code.",
    cues: [
      {
        at: 0.3,
        hold: 9.2,
        kind: "image",
        label: "01 / REAL INBOX",
        text: "Paste the transcript. Click Audit.",
        sub: "A real support transcript, not a canned mock. The model does the reading.",
        image: "01-inbox.png",
        facts: [
          { label: "TURNS", value: "3" },
          { label: "INPUT", value: "support transcript" },
          { label: "NEXT", value: "binding promises" },
        ],
      },
      {
        at: 9.8,
        hold: 9.0,
        kind: "card",
        label: "02 / META CORE",
        text: "Muse Spark Open reads the messy dialogue.",
        sub: "Structured promise objects: action, amount, order, system, confidence, exact quote. No regex.",
        tone: "mint",
        facts: [
          { label: "MODEL", value: "muse-spark-open" },
          { label: "VALIDATION", value: "Pydantic" },
          { label: "REPAIRS", value: "max 2, then fail" },
        ],
      },
      {
        at: 19.2,
        hold: 12.8,
        kind: "image",
        label: "03 / LEDGER JOIN",
        text: "The promise meets the ledger.",
        sub: "The model never decides whether money moved. Reconciliation is deterministic code.",
        image: "03-drift.png",
        imageFit: "contain",
        facts: [
          { label: "PROMISE", value: "$45.00" },
          { label: "SETTLED", value: "$0.00", tone: "alarm" },
          { label: "AT RISK", value: "$45.00", tone: "alarm" },
        ],
      },
      {
        at: 32.4,
        hold: 12.2,
        kind: "image",
        label: "04 / EXPLAIN",
        text: "One sentence a merchant can act on.",
        sub: "A real /explain response, captured live.",
        image: "04-explain.png",
        imageFit: "contain",
        facts: [
          { label: "EXPLAIN", value: "one sentence" },
          { label: "SOURCE", value: "real /explain" },
          { label: "LEDGER", value: "$0.00 settled" },
        ],
      },
    ],
  },
  {
    id: "fix",
    beat: "1:30-2:15 The fix",
    start: 90,
    duration: 45,
    mode: "capture",
    tone: "dark",
    vo: "One click executes the corrective refund against the test ledger. The receipt carries an idempotency key. Click again: same key, original receipt, ledger untouched. A concurrent duplicate is serialized. A charge ceiling stops a forged promise. The card flips to Verified, the recovered total moves to forty-five dollars. That is the firewall: promise, proof, patch.",
    cues: [
      {
        at: 0.3,
        hold: 8.8,
        kind: "image",
        label: "01 / THE FIX",
        text: "One click. One refund.",
        sub: "The shortfall is clamped to the ledger. The receipt carries an idempotency key.",
        image: "03-drift.png",
        imageFit: "contain",
        facts: [
          { label: "ACTION", value: "refund" },
          { label: "AMOUNT", value: "$45.00" },
          { label: "KEY", value: "refund:992:stripe:45.00" },
        ],
      },
      {
        at: 9.5,
        hold: 10.5,
        kind: "image",
        label: "02 / VERIFIED",
        text: "Verified. Recovered.",
        sub: "The drift closes. The recovered total moves to $45.00.",
        image: "05-verified.png",
        facts: [
          { label: "RECOVERED", value: "$45.00" },
          { label: "DRIFT", value: "$0.00" },
          { label: "SECOND CLICK", value: "$0.00 movement" },
        ],
      },
      {
        at: 20.5,
        hold: 13.0,
        kind: "receipt",
        label: "03 / TWO PARTIES",
        text: "Click again. Same key. Zero movement.",
        sub: "The second POST returns the original receipt. No double refund.",
        tone: "mint",
      },
      {
        at: 34.0,
        hold: 10.8,
        kind: "image",
        label: "04 / IN THE BROWSER",
        text: "Signed by Settleye. Countersigned by the merchant.",
        sub: "Both signatures verify locally. Change one digit and the receipt fails.",
        image: "06-receipt.png",
        imageFit: "contain",
        facts: [
          { label: "ISSUER", value: "settleye-demo-2026-12" },
          { label: "MERCHANT", value: "merchant-demo-2026-12" },
          { label: "RECEIPT", value: "sha256:8551...149d44" },
        ],
      },
    ],
  },
  {
    id: "math",
    beat: "2:15-2:45 The numbers",
    start: 135,
    duration: 30,
    mode: "code",
    tone: "dark",
    vo: "The proof is not a projection. Forty-four dollars caught live on one test order in four seconds. Twelve of twelve eval verdicts, eleven of twelve exact entities, zero non-binding promises drifted. Three hundred wild transcripts, zero false binding promises. Every dollar of dispute loss costs four sixty-one all-in. This is evidence, not vibes.",
    cues: [
      {
        at: 0.4,
        hold: 6.0,
        kind: "money",
        label: "LIVE TEST ORDER",
        text: "$44.00",
        sub: "at risk on one test-mode dev-store order (#1001), found in 4.07 seconds. Single order, not a fleet sample.",
        tone: "mint",
      },
      {
        at: 7.0,
        hold: 7.0,
        kind: "money",
        label: "EVAL",
        text: "12 of 12",
        sub: "verdicts correct. 11 of 12 exact entity matches. 0 of 4 non-binding promises drifted.",
        tone: "cream",
      },
      {
        at: 14.8,
        hold: 6.0,
        kind: "money",
        label: "WILD TRANSCRIPTS",
        text: "300 of 300",
        sub: "processed with zero crashes and zero false binding promises.",
        tone: "mint",
      },
      {
        at: 21.4,
        hold: 8.2,
        kind: "money",
        label: "ALL-IN DISPUTE COST",
        text: "$4.61",
        sub: "per $1 of dispute loss, once goods, fees, and labor are added. Evidence, not vibes.",
        tone: "gold",
      },
    ],
  },
  {
    id: "vision",
    beat: "2:45-3:00 Vision plus end card",
    start: 165,
    duration: 15,
    mode: "code",
    tone: "dark",
    vo: "Every payment needs a ledger. Every agent needs an auditor. The nightly sweep catches orders promised across several tickets. Built for this event on Meta open weights.",
    cues: [
      {
        at: 0.3,
        hold: 4.8,
        kind: "line",
        text: "Every payment needs a ledger.",
        sub: "Every agent needs an auditor.",
        tone: "mint",
      },
      {
        at: 5.6,
        hold: 4.0,
        kind: "line",
        text: "The nightly sweep catches orders promised across several tickets.",
        sub: "Built for this event on Meta open weights.",
        tone: "cream",
      },
      {
        at: 9.8,
        hold: 5.2,
        kind: "end",
        text: "Resolved is not settled.",
        tone: "mint",
      },
    ],
  },
];
