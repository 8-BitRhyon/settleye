import { storyboard, DURATION } from "./storyboard.js";

// GSAP is loaded as a global from node_modules (see index.html).
declare const gsap: any;

interface ReceiptData {
  first?: unknown;
  second?: unknown;
  valueBeforeSecond?: unknown;
  valueAfterSecond?: unknown;
}

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
}

async function loadReceipts(): Promise<ReceiptData> {
  try {
    const r = await fetch("capture/receipts.json");
    if (!r.ok) return {};
    return (await r.json()) as ReceiptData;
  } catch {
    return {};
  }
}

function cueHTML(cue: (typeof storyboard)[number]["cues"][number], receipts: ReceiptData): string {
  const tone = `tone-${cue.tone ?? "ink"}`;
  if (cue.kind === "image") {
    return `<div class="capture-frame"><img class="capture-img" src="capture/${cue.image}" alt="">
      <div class="caption"><div class="cap-title ${tone}">${esc(cue.text)}</div><div class="cap-sub">${esc(cue.sub ?? "")}</div></div></div>`;
  }
  if (cue.kind === "receipt") {
    const fmt = (label: string, r: any) => r ? `${label}\n  idempotency_key: "${r.idempotency_key}"\n  amount_usd: ${r.amount_usd}\n  status: "${r.status}"\n  promise: ${r.promise?.action} order #${r.promise?.order_id} (confidence ${r.promise?.confidence})\n  evidence: "${r.promise?.evidence_span}"` : `${label}\n  (missing)`;
    const body = receipts.first
      ? `${fmt("FIRST CLICK - real POST /remediate (UI button)", receipts.first)}\n\n${fmt("SECOND CLICK - SAME KEY - real POST /remediate", receipts.second)}\n\n/value before re-click: ${JSON.stringify(receipts.valueBeforeSecond)}\n/value after re-click:  ${JSON.stringify(receipts.valueAfterSecond)}`
      : "Receipt data missing. Run: npm run capture";
    return `<div class="scene-inner"><div class="receipt"><h3>${esc(cue.text)}</h3><pre>${esc(body)}</pre><div class="sub" style="color:#d4d4d8;font-size:30px">${esc(cue.sub ?? "")}</div></div></div>`;
  }
  if (cue.kind === "money") {
    return `<div class="scene-inner"><div class="rule"></div><div class="display money h-money ${tone}">${esc(cue.text)}</div><div class="sub">${esc(cue.sub ?? "")}</div></div>`;
  }
  if (cue.kind === "card") {
    return `<div class="scene-inner"><div class="card"><div class="kicker ${tone}">${esc(cue.kind === "card" && cue.text === "SETTLEYE" ? "End card" : "Precedent")}</div><div class="display ${tone}" style="margin-top:14px">${esc(cue.text)}</div><div class="sub">${esc(cue.sub ?? "")}</div></div></div>`;
  }
  if (cue.kind === "kicker") {
    return `<div class="scene-inner"><div class="kicker ${tone}">${esc(cue.text)}</div><div class="display h-big" style="margin-top:20px">Settleye</div><div class="sub">${esc(cue.sub ?? "")}</div></div>`;
  }
  return `<div class="scene-inner"><div class="rule"></div><div class="display h-line ${tone}">${esc(cue.text)}</div><div class="sub">${esc(cue.sub ?? "")}</div></div>`;
}

async function boot(): Promise<void> {
  const receipts = await loadReceipts();
  const stage = document.getElementById("stage")!;
  const bar = document.querySelector(".progress-bar") as HTMLElement;
  const tc = document.querySelector(".timecode") as HTMLElement;

  const tl = gsap.timeline({ paused: true, defaults: { ease: "power3.out" } });

  for (const scene of storyboard) {
    const el = document.createElement("section");
    el.className = "scene";
    el.id = `scene-${scene.id}`;
    el.innerHTML = scene.cues
      .map((c, i) => `<div class="cue" data-cue="${i}" style="position:absolute;inset:0;opacity:0;visibility:hidden">${cueHTML(c, receipts)}</div>`)
      .join("");
    stage.appendChild(el);

    tl.set(el, { autoAlpha: 1 }, scene.start);
    tl.set(el, { autoAlpha: 0 }, scene.start + scene.duration - 0.01);

    scene.cues.forEach((cue, i) => {
      const sel = `#scene-${scene.id} [data-cue="${i}"]`;
      const t0 = scene.start + cue.at;
      tl.set(sel, { autoAlpha: 1 }, t0);
      const inner = `${sel} .scene-inner, ${sel} .capture-frame`;
      tl.fromTo(inner, { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }, t0);
      if (cue.kind === "image") {
        tl.fromTo(`${sel} .capture-img`, { scale: 1.0 }, { scale: 1.055, duration: cue.hold + 0.8, ease: "none" }, t0);
        tl.fromTo(`${sel} .caption`, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.5 }, t0 + 0.15);
      }
      // Hold, then fade this cue out just before the next one / scene end.
      const end = i + 1 < scene.cues.length ? scene.start + scene.cues[i + 1].at : scene.start + scene.duration;
      tl.to(sel, { autoAlpha: 0, duration: 0.35, ease: "power2.in" }, Math.max(t0 + 0.6, end - 0.35));
    });
  }

  tl.pause(0);

  (window as any).__film = {
    duration: DURATION,
    // GSAP suppresses tween callbacks on seek, so drive progress/timecode
    // directly from the seek target: frame-stepping stays deterministic.
    seek: (t: number) => {
      const clamped = Math.min(Math.max(t, 0), DURATION - 0.001);
      tl.pause(clamped);
      bar.style.width = `${(clamped / DURATION) * 100}%`;
      const m = Math.floor(clamped / 60); const s = Math.floor(clamped % 60);
      tc.textContent = `${m}:${String(s).padStart(2, "0")} / 3:00`;
    },
    ready: true,
  };
}

boot();
