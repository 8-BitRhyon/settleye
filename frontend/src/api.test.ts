import { afterEach, describe, expect, it, vi } from "vitest";
import { explainDrift } from "./api";

const DRIFT = {
  promise: {
    action: "refund",
    amount: 45,
    order_id: "992",
    target_system: "stripe",
    asserted_state: "full refund processed",
    confidence: 0.9,
    evidence_span: "processed",
  },
  verdict: "drift" as const,
  ledger_summary: "Order 992: $0.00 settled of $45.00 promised.",
  amount_at_risk_usd: 45,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("explainDrift", () => {
  it("posts the drift and returns the explanation", async () => {
    const fetch = vi.fn(async () =>
      Response.json({ explanation: "The $45 was promised but never settled." }),
    );
    vi.stubGlobal("fetch", fetch);
    const text = await explainDrift(
      DRIFT.promise as never,
      DRIFT.ledger_summary,
      DRIFT.amount_at_risk_usd,
    );
    expect(text).toContain("$45");
    expect(fetch).toHaveBeenCalledOnce();
    const call = fetch.mock.calls[0] as unknown as [string, RequestInit];
    const [url, init] = call;
    expect(url).toMatch(/\/explain$/);
    expect(JSON.parse(init.body as string).amount_usd).toBe(45);
  });

  it("throws the server detail when the model has nothing to say", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json({ detail: "Model returned no explanation text." }, { status: 422 }),
      ),
    );
    await expect(
      explainDrift(DRIFT.promise as never, DRIFT.ledger_summary, 45),
    ).rejects.toThrow("no explanation");
  });
});
