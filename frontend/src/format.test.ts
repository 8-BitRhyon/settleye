import { describe, expect, it } from "vitest";
import {
  AUDIT_LOADING_LABEL,
  SAMPLE_PHANTOM_TRANSCRIPT,
  formatUSD,
  verdictClasses,
  verdictLabel,
} from "./format";

describe("formatUSD", () => {
  it("renders two decimals with a dollar sign", () => {
    expect(formatUSD(45)).toBe("$45.00");
    expect(formatUSD(0)).toBe("$0.00");
  });
});

describe("verdict labels", () => {
  it("never exposes raw enum strings", () => {
    expect(verdictLabel("verified")).toBe("Verified");
    expect(verdictLabel("drift")).toBe("State drift");
    expect(verdictLabel("unverifiable")).toBe("Needs review");
    expect(verdictLabel("not_binding")).toBe("Not binding");
  });

  it("drift is the only red verdict", () => {
    expect(verdictClasses("drift")).toContain("red");
    expect(verdictClasses("verified")).not.toContain("red");
    expect(verdictClasses("unverifiable")).not.toContain("red");
    expect(verdictClasses("not_binding")).not.toContain("red");
  });
});

describe("inbox copy", () => {
  it("loading label and sample transcript exist", () => {
    expect(AUDIT_LOADING_LABEL.length).toBeGreaterThan(0);
    expect(SAMPLE_PHANTOM_TRANSCRIPT).toContain("#992");
  });
});
