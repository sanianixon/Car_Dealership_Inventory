/** Add units to a vehicle's stock. Admin only. */

import { useState, type FormEvent } from "react";

import { ApiError } from "../api";
import type { Vehicle } from "../types";

interface Props {
  vehicle: Vehicle;
  error: ApiError | Error | null;
  busy: boolean;
  onSubmit: (quantity: number) => void;
}

export function RestockForm({ vehicle, error, busy, onSubmit }: Props) {
  const [quantity, setQuantity] = useState("1");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit(Number(quantity));
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <p className="text-sm text-forecourt-500">
        {vehicle.make} {vehicle.model} currently has{" "}
        <strong className="text-forecourt-900">{vehicle.quantity}</strong> in stock.
      </p>

      <div>
        <label htmlFor="restockQuantity" className="mb-1.5 block text-sm font-medium">
          Units to add
        </label>
        <input
          id="restockQuantity"
          type="number"
          min="1"
          step="1"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
          className="w-full rounded-lg border border-forecourt-300 px-3 py-2.5 focus:border-petrol-600 focus:outline-none"
        />
        {error instanceof ApiError && error.fieldError("quantity") && (
          <p className="mt-1.5 text-sm text-tag-red">{error.fieldError("quantity")}</p>
        )}
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2.5 text-sm text-tag-red">
          {error.message}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded-lg bg-petrol-600 px-4 py-2.5 font-semibold text-white transition hover:bg-petrol-700 disabled:opacity-60"
      >
        {busy ? "Restocking…" : "Add to stock"}
      </button>
    </form>
  );
}
