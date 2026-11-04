import { storyboard, DURATION, MODEL_ID, REPO_URL } from "./storyboard.js";

declare const gsap: any;

interface ReceiptData {
  first?: any;
  second?: any;
  valueBeforeSecond?: any;
  valueAfterSecond?: any;
}

interface SampleReceipt {
  receipt_id?: string;
  issuer?: { key_id?: string };
  promise?: { amount?: string; order_id?: string };
  ledger?: { system?: string };
  remediation?: { idempotency_key?: string; amount_usd?: string; status?: string };
  signature?: { public_key?: string };
  countersignatures?: Array<{ key_id?: string; public_key?: string }>;
}

type Cue = (typeof storyboard)[number]["cues"][number];

function esc(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function loadJSON<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path);
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function orbit(): string {
  return `<svg viewBox="0 0 1920 1080" fill="none" aria-hidden="true">
    <g stroke="currentColor" stroke-width="1">
      <circle cx="1540" cy="280" r="270" stroke-dasharray="3 8" opacity=".55"/>
      <circle cx="1540" cy="280" r="390" opacity=".3"/>
      <circle cx="1540" cy="280" r="510" stroke-dasharray="1 14" opacity=".22"/>
    </g>
    <circle cx="1810" cy="280" r="4" fill="#9fd8c2"/>
  </svg>`;
}

function toneClass(tone?: string): string {
  return tone ? `tone-${tone}` : "";
}

function artRows(cue: Cue): string {
  if (!cue.facts?.length) return "";
  return cue.facts
    .map(
      (fact) =>
        `<div class="art-row"><span>${esc(fact.label)}</span><b class="${toneClass(fact.tone)}">${esc(fact.value)}</b></div>`,
    )
    .join("");
}

function factRows(cue: Cue): string {
  if (!cue.facts?.length) return "";
  return `<div class="facts">${cue.facts
    .map(
      (fact) =>
        `<div class="fact"><span>${esc(fact.label)}</span><b class="${toneClass(fact.tone)}">${esc(fact.value)}</b></div>`,
    )
    .join("")}</div>`;
}

function heroHTML(cue: Cue): string {
  return `<div class="scene-inner">
    <div class="hero-grid">
      <div class="hero-copy">
        <div class="kicker">EXECUTION AUDITOR</div>
        <h1>${esc(cue.text)}${cue.highlight ? `<br><em>${esc(cue.highlight)}</em>` : ""}</h1>
        <div class="sub">${esc(cue.sub ?? "")}</div>
      </div>
      <div class="hero-art">
        <div class="art-head"><i></i><i></i><i></i><span>SETTLEYE / EXCEPTION INBOX</span></div>
        ${artRows(cue)}
        <div class="art-foot">order #992 · 3 turns · checked against the ledger</div>
      </div>
    </div>
  </div>`;
}

function imageHTML(cue: Cue): string {
  const fitClass = cue.imageFit === "contain" ? " contain" : "";
  const position = cue.imagePosition ?? "top center";
  return `<div class="scene-inner">
    <div class="capture-split">
      <div class="window">
        <div class="window-bar"><i></i><i></i><i></i><span>settleye / exception inbox</span></div>
        <div class="window-body${fitClass}"><img src="capture/${cue.image}" alt="" style="object-position:${position}"></div>
      </div>
      <div class="rail">
        <div class="kicker">${esc(cue.label ?? "LIVE CAPTURE")}</div>
        <h2>${esc(cue.text)}</h2>
        <p>${esc(cue.sub ?? "")}</p>
        ${factRows(cue)}
      </div>
    </div>
  </div>`;
}

function receiptHTML(cue: Cue, sample: SampleReceipt | null, receipts: ReceiptData): string {
  const receiptId = sample?.receipt_id ?? "sha256:8551a4d8...149d44";
  const key =
    sample?.remediation?.idempotency_key ??
    receipts.first?.idempotency_key ??
    "refund:992:stripe:45.00";
  const amount =
    sample?.remediation?.amount_usd ?? receipts.first?.amount_usd ?? "45.00";
  const issuer = sample?.issuer?.key_id ?? "settleye-demo-2026-12";
  const merchant =
    sample?.countersignatures?.[0]?.key_id ?? "merchant-demo-2026-12";
  const second = receipts.second;
  const secondStatus = second?.status ?? "already_executed";
  const secondKey = sample?.remediation?.idempotency_key ?? second?.idempotency_key ?? key;
  return `<div class="scene-inner">
    <div class="receipt-split">
      <div class="receipt-card">
        <div class="receipt-head">
          <div class="kicker">EXECUTION RECEIPT</div>
          <div class="receipt-id">${esc(receiptId)}</div>
        </div>
        <div class="receipt-amount">$${esc(amount)}</div>
        <div class="receipt-meta">refund · order #992 · stripe</div>
        <div class="receipt-key">${esc(key)}</div>
        <div class="sig-list">
          <div class="sig-row"><div class="sig-check">✓</div><div><div class="sig-title">Issuer signature valid</div><div class="sig-key">${esc(issuer)}</div></div></div>
          <div class="sig-row"><div class="sig-check">✓</div><div><div class="sig-title">Merchant countersigned</div><div class="sig-key">${esc(merchant)}</div></div></div>
        </div>
        <div class="receipt-foot">Transcript digest · promise · ledger observation · remediation key. Change one digit and the signature fails.</div>
      </div>
      <div class="proof-card">
        <div class="proof-label">SECOND CLICK / REAL RESPONSE</div>
        <div class="proof-status">${esc(secondStatus)}</div>
        <div class="proof-key">${esc(secondKey)}</div>
        <div class="proof-zero">$0.00 additional movement</div>
        <div class="proof-note">Same key. Original receipt. Ledger untouched.</div>
      </div>
    </div>
  </div>`;
}

function cueHTML(cue: Cue, sample: SampleReceipt | null, receipts: ReceiptData): string {
  if (cue.kind === "hero") return heroHTML(cue);
  if (cue.kind === "image") return imageHTML(cue);
  if (cue.kind === "receipt") return receiptHTML(cue, sample, receipts);
  if (cue.kind === "card") {
    return `<div class="scene-inner"><div class="case-card"><div class="case-label">${esc(cue.label ?? "CASE")}</div><div class="display ${toneClass(cue.tone)}">${esc(cue.text)}</div><div class="sub">${esc(cue.sub ?? "")}</div>${factRows(cue)}</div></div>`;
  }
  if (cue.kind === "money") {
    return `<div class="scene-inner"><div class="stat-layout"><div class="kicker">${esc(cue.label ?? "THE PROOF")}</div><div class="stat-value ${toneClass(cue.tone)}">${esc(cue.text)}</div><div class="stat-sub">${esc(cue.sub ?? "")}</div></div></div>`;
  }
  if (cue.kind === "end") {
    return `<div class="scene-inner"><div class="end-layout"><div class="end-title">Resolved is <em>not settled.</em></div><div class="end-rule"></div><div class="end-sub">EXECUTION AUDITOR FOR AI SUPPORT AGENTS</div><div class="end-links"><span class="end-pill">Open the sample</span><span class="end-url">8-bitrhyon.github.io/settleye/index.html?sample=1</span></div><div class="end-url" style="margin-top:18px">${esc(REPO_URL)} · ${esc(MODEL_ID)}</div></div></div>`;
  }
  return `<div class="scene-inner"><div class="rule"></div><div class="display h-line ${toneClass(cue.tone)}">${esc(cue.text)}</div><div class="sub">${esc(cue.sub ?? "")}</div></div>`;
}

async function boot(): Promise<void> {
  const [receipts, sample] = await Promise.all([
    loadJSON<ReceiptData>("capture/receipts.json"),
    loadJSON<SampleReceipt>("capture/sample-receipt.json"),
  ]);
  const stage = document.getElementById("stage")!;
  const bar = document.querySelector(".progress-bar") as HTMLElement;
  const tc = document.querySelector(".timecode") as HTMLElement;
  const data = receipts ?? {};

  const tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });

  for (const scene of storyboard) {
    const el = document.createElement("section");
    el.className = `scene scene-${scene.tone}`;
    el.id = `scene-${scene.id}`;
    el.innerHTML =
      `<div class="scene-orbit">${orbit()}</div>` +
      scene.cues
        .map(
          (cue, index) =>
            `<div class="cue" data-cue="${index}" style="position:absolute;inset:0;opacity:0;visibility:hidden">${cueHTML(cue, sample, data)}</div>`,
        )
        .join("");
    stage.appendChild(el);

    tl.set(el, { autoAlpha: 1 }, scene.start);
    tl.set(el, { autoAlpha: 0 }, scene.start + scene.duration - 0.01);

    scene.cues.forEach((cue, index) => {
      const selector = `#scene-${scene.id} [data-cue="${index}"]`;
      const t0 = scene.start + cue.at;
      tl.set(selector, { autoAlpha: 1 }, t0);
      tl.fromTo(
        `${selector} .scene-inner`,
        { autoAlpha: 0, y: 28 },
        { autoAlpha: 1, y: 0, duration: 0.7, ease: "power2.out" },
        t0,
      );
      if (cue.kind === "image") {
        tl.fromTo(
          `${selector} .window`,
          { scale: 0.985, autoAlpha: 0 },
          { scale: 1, autoAlpha: 1, duration: 0.7, ease: "power2.out" },
          t0,
        );
        tl.fromTo(
          `${selector} .window img`,
          { scale: 1.02 },
          { scale: 1.065, duration: cue.hold + 1, ease: "none" },
          t0,
        );
        tl.fromTo(
          `${selector} .rail`,
          { x: 22, autoAlpha: 0 },
          { x: 0, autoAlpha: 1, duration: 0.65, ease: "power2.out" },
          t0 + 0.08,
        );
      }
      if (cue.kind === "hero") {
        tl.fromTo(
          `${selector} .hero-art`,
          { x: 18, autoAlpha: 0 },
          { x: 0, autoAlpha: 1, duration: 0.8, ease: "power2.out" },
          t0 + 0.12,
        );
      }
      if (cue.kind === "receipt") {
        tl.fromTo(
          `${selector} .receipt-card`,
          { x: -18, autoAlpha: 0 },
          { x: 0, autoAlpha: 1, duration: 0.7, ease: "power2.out" },
          t0,
        );
        tl.fromTo(
          `${selector} .proof-card`,
          { x: 18, autoAlpha: 0 },
          { x: 0, autoAlpha: 1, duration: 0.7, ease: "power2.out" },
          t0 + 0.08,
        );
      }
      const end =
        index + 1 < scene.cues.length
          ? scene.start + scene.cues[index + 1].at
          : scene.start + scene.duration;
      tl.to(
        selector,
        { autoAlpha: 0, duration: 0.35, ease: "power2.in" },
        Math.max(t0 + 0.7, end - 0.35),
      );
    });
  }

  tl.pause(0);

  const toneAt = (t: number) =>
    storyboard.find((scene) => t >= scene.start && t < scene.start + scene.duration)?.tone ?? "dark";

  (window as any).__film = {
    duration: DURATION,
    seek: (t: number) => {
      const clamped = Math.min(Math.max(t, 0), DURATION - 0.001);
      tl.pause(clamped);
      bar.style.width = `${(clamped / DURATION) * 100}%`;
      const m = Math.floor(clamped / 60);
      const s = Math.floor(clamped % 60);
      tc.textContent = `${m}:${String(s).padStart(2, "0")} / 3:00`;
      stage.dataset.tone = toneAt(clamped);
      stage.style.setProperty("--orbit-rotate", `${(clamped / DURATION) * 360}deg`);
    },
    ready: true,
  };
}

boot();
