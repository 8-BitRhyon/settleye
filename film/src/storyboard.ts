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
    | "fleet"
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
    vo: "Your AI agent told the customer, 'Your refund is processed.' The ticket closed. The ledger says zero dollars moved. The agent isn't lying. It just never checked. That gap is what we audit. I'm Rhyon. This is Settleye.",
    cues: [
      {
        at: 0.3,
        hold: 8.6,
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
        at: 8.9,
        hold: 4.1,
        kind: "line",
        text: "The agent isn't lying.",
        sub: "It just never checked.",
        tone: "ink",
      },
      {
        at: 13.0,
        hold: 6.7,
        kind: "money",
        label: "THE GAP",
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
    vo: "Air Canada's chatbot invented a refund policy. A tribunal made them honor it. Priceline's bot promised refunds on bookings that weren't refundable. One phantom refund a week costs twenty-three hundred forty dollars a year. Add chargebacks, and it's closer to four thousand seven hundred. The industry grades the conversation. The customer waits for the money.",
    cues: [
      {
        at: 0.0,
        hold: 5.4,
        kind: "card",
        label: "PRECEDENT / 01",
        text: "Air Canada",
        sub: "The chatbot invented a refund policy. A tribunal made them honor it.",
        tone: "alarm",
      },
      {
        at: 5.4,
        hold: 4.8,
        kind: "card",
        label: "PRECEDENT / 02",
        text: "Priceline",
        sub: "The bot promised refunds on non-refundable bookings.",
        tone: "alarm",
      },
      {
        at: 10.2,
        hold: 4.7,
        kind: "money",
        label: "ONE A WEEK",
        text: "$2,340 / year",
        sub: "One phantom refund a week leaks $2,340 a year per merchant.",
        tone: "cream",
      },
      {
        at: 14.9,
        hold: 4.3,
        kind: "money",
        label: "WITH CHARGEBACKS",
        text: "$4,700 all-in",
        sub: "The refund, the fee, the labor, and the customer you lose.",
        tone: "alarm",
      },
      {
        at: 19.2,
        hold: 5.5,
        kind: "line",
        text: "The industry grades the conversation.",
        sub: "The customer waits for the money.",
        tone: "cream",
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
    vo: "Watch the screen. The transcript is messy. The model reads it and returns structured promises: the action, the amount, the order, the system, and the exact quote. That's the only job the model has. No regex. No guessing. Every reply is validated. If it doesn't fit the format, it fails loudly. Then a separate check compares the promise to the ledger. Here's the drift: the promise says forty-five dollars. The ledger says zero. The model never decides whether money moved. The ledger does.",
    cues: [
      {
        at: 0.0,
        hold: 4.0,
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
        at: 4.1,
        hold: 18.2,
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
        at: 22.4,
        hold: 10.0,
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
    vo: "Here's the fix. One click refunds the exact shortfall against the test ledger. The receipt carries a retry key. Click again, and you get the same receipt. No second refund. Two clicks at once still produce one refund. A charge ceiling blocks a promise bigger than the order. The receipt is signed by Settleye and countersigned by the merchant. Change one digit, and the signature fails. The card flips to Verified. The recovered total moves to forty-five dollars. That's the firewall: promise, proof, patch.",
    cues: [
      {
        at: 0.0,
        hold: 6.7,
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
        at: 6.8,
        hold: 20.9,
        kind: "receipt",
        label: "03 / TWO PARTIES",
        text: "Click again. Same key. Zero movement.",
        sub: "The second POST returns the original receipt. No double refund.",
        tone: "mint",
      },
      {
        at: 27.9,
        hold: 6.7,
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
        at: 34.7,
        hold: 10.0,
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
    vo: "The proof isn't a projection. Forty-four dollars caught live on one test order, in four seconds. Twelve of twelve eval verdicts. Eleven of twelve entities exact. Zero of eight real promises missed. Three hundred wild transcripts. Zero false binding promises. Then the fleet model: one hundred twenty-four thousand at ten thousand tickets. Twelve point five million at a million. Stated assumptions, not a guarantee.",
    cues: [
      {
        at: 0.0,
        hold: 2.2,
        kind: "line",
        text: "The proof isn't a projection.",
        sub: "Measured first. Modeled second.",
        tone: "cream",
      },
      {
        at: 2.3,
        hold: 4.2,
        kind: "money",
        label: "TIER 1 / LIVE, READ-ONLY",
        text: "$44.00",
        sub: "at risk on one test-mode dev-store order (#1001), found in 4.07 seconds. No money moved. Single order, not a fleet sample.",
        tone: "mint",
      },
      {
        at: 6.6,
        hold: 6.4,
        kind: "money",
        label: "TIER 2 / LABELED EVAL",
        text: "12 of 12",
        sub: "verdicts correct. 11 of 12 exact entities. 0 of 8 binding cases missed. 0 of 4 non-binding drifts.",
        tone: "cream",
      },
      {
        at: 14.0,
        hold: 3.6,
        kind: "money",
        label: "WILD TRANSCRIPTS",
        text: "300 of 300",
        sub: "processed with zero crashes and zero false binding promises.",
        tone: "mint",
      },
      {
        at: 17.7,
        hold: 12.2,
        kind: "fleet",
        label: "TIER 3 / MODELED, NOT MEASURED",
        text: "$124K to $12.5M",
        sub: "modeled annual exposure protected across 10,000 to 1,000,000 tickets per month.",
        highlight: "Assumptions: 10.6% refund intent, 66.7% binding, 4.0% execution failure, $52.50 refund, 4.61x dispute cost, $128 fee. Modeled, not measured.",
        facts: [
          { label: "10,000 / mo", value: "$124,328.40", tone: "cream" },
          { label: "100,000 / mo", value: "$1,256,604.96", tone: "cream" },
          { label: "1,000,000 / mo", value: "$12,557,168.40", tone: "mint" },
        ],
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
    vo: "Every payment needs a ledger. Every agent needs an auditor. A nightly sweep catches orders promised across several tickets. Built for this event on Meta open weights.",
    cues: [
      {
        at: 0.0,
        hold: 4.7,
        kind: "line",
        text: "Every payment needs a ledger.",
        sub: "Every agent needs an auditor.",
        tone: "mint",
      },
      {
        at: 4.8,
        hold: 4.2,
        kind: "line",
        text: "The nightly sweep catches orders promised across several tickets.",
        sub: "Built for this event on Meta open weights.",
        tone: "cream",
      },
      {
        at: 9.0,
        hold: 6.0,
        kind: "end",
        text: "Resolved is not settled.",
        tone: "mint",
      },
    ],
  },
];
