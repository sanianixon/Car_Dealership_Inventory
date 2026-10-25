/** Tests for price and date formatting. */

import { describe, expect, it } from "vitest";

import { formatDate, formatPrice, timeOnLot } from "./format";

describe("formatPrice", () => {
  it("groups digits the Indian way, not the American way", () => {
    // The distinction this function exists for: en-US would render 1,850,000.
    expect(formatPrice(1850000)).toBe("₹18,50,000");
    expect(formatPrice(650000)).toBe("₹6,50,000");
  });

  it("groups at the crore for larger amounts", () => {
    expect(formatPrice(12500000)).toBe("₹1,25,00,000");
  });

  it("drops paise, which no forecourt quotes", () => {
    expect(formatPrice(649999.6)).toBe("₹6,50,000");
  });

  it("handles a free vehicle without breaking", () => {
    expect(formatPrice(0)).toBe("₹0");
  });
});

describe("formatDate", () => {
  it("writes an ISO date as a readable Indian date", () => {
    expect(formatDate("2026-03-14")).toBe("14 Mar 2026");
  });

  it("does not shift the day across the date line", () => {
    // new Date("2026-01-01") parses as UTC midnight, which is 31 December in
    // any timezone behind Greenwich. Parsing the parts avoids that.
    expect(formatDate("2026-01-01")).toBe("1 Jan 2026");
  });

  it("returns the input unchanged when it is not a date", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});

describe("timeOnLot", () => {
  /** A local ISO date. toISOString() would give the UTC day, which is a
   *  different date for most of the day in any timezone offset from GMT. */
  const isoDaysAgo = (days: number) => {
    const date = new Date();
    date.setDate(date.getDate() - days);
    const pad = (part: number) => String(part).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  };

  it("counts a fresh arrival", () => {
    expect(timeOnLot(isoDaysAgo(0))).toBe("arrived today");
  });

  it("uses the singular for one day", () => {
    expect(timeOnLot(isoDaysAgo(1))).toBe("1 day on the lot");
  });

  it("counts in days up to two months", () => {
    expect(timeOnLot(isoDaysAgo(21))).toBe("21 days on the lot");
  });

  it("switches to months once days stop being useful", () => {
    expect(timeOnLot(isoDaysAgo(120))).toBe("4 months on the lot");
  });
});
