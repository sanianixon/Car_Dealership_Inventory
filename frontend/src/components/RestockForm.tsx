/**
 * Take another car of this model onto the lot. Admin only.
 *
 * Restocking a used-car dealership is not raising a number: it is a specific
 * car arriving, with its own year, colour, history and price. One car at a
 * time, because that is how they arrive.
 */

import { useState, type FormEvent } from "react";

import { ApiError } from "../api";
import type { UnitDraft, Vehicle } from "../types";

const FIELD =
  "w-full border border-ink-200 bg-surface px-3 py-2.5 text-ink-900 " +
  "focus:border-clay-600 focus:outline-none";
const LABEL = "mb-1 block text-xs font-semibold uppercase tracking-widest text-ink-500";

interface Props {
  vehicle: Vehicle;
  error: ApiError | Error | null;
  busy: boolean;
  onSubmit: (units: UnitDraft[]) => void;
}

export function RestockForm({ vehicle, error, busy, onSubmit }: Props) {
  const [year, setYear] = useState("");
  const [colour, setColour] = useState("");
  const [price, setPrice] = useState("");
  const [owners, setOwners] = useState("1");
  const [acquiredOn, setAcquiredOn] = useState(new Date().toISOString().slice(0, 10));

  const fieldError = (path: string) =>
    error instanceof ApiError
      ? error.fieldError(path) ?? error.fieldError(`units.0.${path}`)
      : undefined;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit([
      {
        year: Number(year),
        colour: colour.trim(),
        price: Number(price),
        ownershipNumber: Number(owners),
        acquiredOn,
      },
    ]);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <p className="text-sm text-ink-500">
        {vehicle.make} {vehicle.model} currently has{" "}
        <strong className="text-ink-900">{vehicle.quantity}</strong> on the lot.
      </p>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="restockYear" className={LABEL}>
            Build year
          </label>
          <input
            id="restockYear"
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className={FIELD}
          />
          {fieldError("year") && (
            <p className="mt-1.5 text-sm text-clay-700">{fieldError("year")}</p>
          )}
        </div>
        <div>
          <label htmlFor="restockColour" className={LABEL}>
            Colour
          </label>
          <input
            id="restockColour"
            value={colour}
            onChange={(e) => setColour(e.target.value)}
            className={FIELD}
          />
          {fieldError("colour") && (
            <p className="mt-1.5 text-sm text-clay-700">{fieldError("colour")}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="restockPrice" className={LABEL}>
          Price (₹)
        </label>
        <input
          id="restockPrice"
          type="number"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          className={FIELD}
        />
        {fieldError("price") && (
          <p className="mt-1.5 text-sm text-clay-700">{fieldError("price")}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="restockOwners" className={LABEL}>
            Ownership number
          </label>
          <input
            id="restockOwners"
            type="number"
            min="1"
            value={owners}
            onChange={(e) => setOwners(e.target.value)}
            className={FIELD}
          />
        </div>
        <div>
          <label htmlFor="restockAcquired" className={LABEL}>
            Date acquired
          </label>
          <input
            id="restockAcquired"
            type="date"
            value={acquiredOn}
            onChange={(e) => setAcquiredOn(e.target.value)}
            className={FIELD}
          />
        </div>
      </div>

      {error && (
        <p
          role="alert"
          className="border-l-2 border-clay-600 bg-clay-50 px-3 py-2.5 text-sm text-clay-700"
        >
          {error.message}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="w-full bg-ink-900 px-4 py-3 text-xs font-semibold uppercase tracking-widest text-paper transition hover:bg-clay-600 disabled:opacity-50"
      >
        {busy ? "Adding…" : "Add this car to the lot"}
      </button>
    </form>
  );
}
