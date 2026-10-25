/**
 * One actual car on the lot, with the history that makes it different from the
 * car parked next to it: build year, colour, how many owners, how long it has
 * been here, and its own price.
 */

import { formatDate, formatPrice, ownership, timeOnLot } from "../format";
import type { VehicleUnit } from "../types";

interface Props {
  unit: VehicleUnit;
  busy: boolean;
  onPurchase: (unit: VehicleUnit) => void;
}

export function UnitCard({ unit, busy, onPurchase }: Props) {
  const sold = !unit.isAvailable;

  return (
    <article
      className={
        "flex flex-col border p-5 transition " +
        (sold
          ? "border-ink-100 bg-paper"
          : "border-ink-200 bg-surface hover:border-ink-900")
      }
    >
      <header className="mb-4 flex items-baseline justify-between gap-3">
        <span className="tabular text-2xl font-extrabold leading-none tracking-tight">
          {unit.year}
        </span>
        <span className="truncate text-xs font-semibold uppercase tracking-[0.15em] text-ink-500">
          {unit.colour}
        </span>
      </header>

      <dl className="mb-4 space-y-1.5 border-y border-ink-100 py-3 text-xs">
        <div className="flex justify-between gap-3">
          <dt className="text-ink-500">Ownership</dt>
          <dd className="font-semibold">{ownership(unit.ownershipNumber)}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-ink-500">On the lot since</dt>
          <dd className="text-right font-semibold">{formatDate(unit.acquiredOn)}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-ink-500" />
          <dd className="text-right text-ink-500">{timeOnLot(unit.acquiredOn)}</dd>
        </div>
      </dl>

      <p
        className={
          "tabular mb-4 mt-auto text-3xl font-extrabold leading-none tracking-tighter " +
          (sold ? "text-ink-300 line-through" : "text-ink-900")
        }
      >
        {formatPrice(unit.price)}
      </p>

      <button
        type="button"
        onClick={() => onPurchase(unit)}
        disabled={sold || busy}
        title={sold ? "This car has already been sold" : undefined}
        className={
          "w-full px-4 py-2.5 text-xs font-semibold uppercase tracking-widest transition " +
          (sold
            ? "cursor-not-allowed border border-ink-200 text-ink-300"
            : "bg-ink-900 text-paper hover:bg-clay-600 disabled:opacity-50")
        }
      >
        {sold ? "Sold" : busy ? "Working…" : "Buy this one"}
      </button>
    </article>
  );
}
