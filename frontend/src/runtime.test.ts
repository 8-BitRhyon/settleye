import { describe, expect, it } from "vitest";
import { isStaticDemo } from "./runtime";

describe("isStaticDemo", () => {
  it("keeps the live audit available on local hosts", () => {
    expect(isStaticDemo("localhost", undefined)).toBe(false);
    expect(isStaticDemo("127.0.0.1", undefined)).toBe(false);
    expect(isStaticDemo("::1", undefined)).toBe(false);
  });

  it("treats the public static host as a sample-only demo", () => {
    expect(isStaticDemo("8-bitrhyon.github.io", undefined)).toBe(true);
  });

  it("enables the live audit when a hosted API URL is configured", () => {
    expect(
      isStaticDemo("8-bitrhyon.github.io", "https://api.example.com"),
    ).toBe(false);
  });

  it("does not claim a mode when the host is unknown", () => {
    expect(isStaticDemo("", undefined)).toBe(false);
  });
});
