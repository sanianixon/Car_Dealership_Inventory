/**
 * Display formatting, in one place so every price and date in the app reads
 * the same way.
 *
 * The locale is en-IN throughout. That matters for more than the symbol:
 * Indian digit grouping puts separators at the lakh and crore, so 1850000
 * renders as ₹18,50,000 rather than ₹1,850,000. Using en-US with an INR
 * currency would show the symbol but group the digits wrongly.
 */

const rupees = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const shortDate = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

/** A price as rupees, with Indian digit grouping and no paise. */
export function formatPrice(amount: number): string {
  return rupees.format(amount);
}

/**
 * An ISO date (YYYY-MM-DD) as a readable Indian date, e.g. "16 Oct 2026".
 *
 * Parsed as a plain date rather than through `new Date(iso)`, which treats a
 * bare date string as UTC midnight and can therefore show the previous day for
 * anyone west of Greenwich.
 */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  if (!year || !month || !day) return iso;
  return shortDate.format(new Date(year, month - 1, day));
}

/** How long a vehicle has been on the forecourt, in plain words. */
export function timeOnLot(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  if (!year || !month || !day) return "";

  // Both ends are reduced to local midnight before subtracting. Comparing a
  // midnight against the current time leaves a fraction of a day, which rounds
  // to an extra day for anyone looking at the page after midday.
  const acquired = new Date(year, month - 1, day);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.max(
    0,
    Math.round((today.getTime() - acquired.getTime()) / 86_400_000),
  );

  if (days === 0) return "arrived today";
  if (days === 1) return "1 day on the lot";
  if (days < 60) return `${days} days on the lot`;
  const months = Math.round(days / 30);
  return `${months} months on the lot`;
}

/** "1st owner", "2nd owner", "3rd owner" — how used-car listings phrase it. */
export function ownership(count: number): string {
  const suffix =
    count % 100 >= 11 && count % 100 <= 13
      ? "th"
      : ({ 1: "st", 2: "nd", 3: "rd" }[count % 10] ?? "th");
  return `${count}${suffix} owner`;
}
