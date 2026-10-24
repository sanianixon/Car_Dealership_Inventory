/**
 * Add or edit a vehicle. Admin only.
 *
 * On edit this sends only the fields that actually changed, which is why the
 * API accepts a partial body: an untouched field is not resubmitted and so
 * cannot be clobbered by a stale value.
 */

import { useState, type FormEvent } from "react";

import { ApiError } from "../api";
import type { Vehicle } from "../types";

export interface VehicleDraft {
  make: string;
  model: string;
  category: string;
  price: string;
  quantity: string;
}

const BLANK: VehicleDraft = { make: "", model: "", category: "", price: "", quantity: "" };

function draftFrom(vehicle: Vehicle | null): VehicleDraft {
  if (vehicle === null) return BLANK;
  return {
    make: vehicle.make,
    model: vehicle.model,
    category: vehicle.category,
    price: String(vehicle.price),
    quantity: String(vehicle.quantity),
  };
}

const FIELDS: { key: keyof VehicleDraft; label: string; type: string }[] = [
  { key: "make", label: "Make", type: "text" },
  { key: "model", label: "Model", type: "text" },
  { key: "category", label: "Category", type: "text" },
  { key: "price", label: "Price", type: "number" },
  { key: "quantity", label: "Quantity in stock", type: "number" },
];

interface Props {
  /** null means "create a new vehicle". */
  vehicle: Vehicle | null;
  error: ApiError | Error | null;
  busy: boolean;
  onSubmit: (values: Record<string, string | number>) => void;
}

export function VehicleForm({ vehicle, error, busy, onSubmit }: Props) {
  const [draft, setDraft] = useState<VehicleDraft>(() => draftFrom(vehicle));
  const original = draftFrom(vehicle);

  const fieldError = (path: string) =>
    error instanceof ApiError ? error.fieldError(path) : undefined;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const numeric = new Set(["price", "quantity"]);
    const values: Record<string, string | number> = {};

    for (const { key } of FIELDS) {
      const value = draft[key].trim();
      // On edit, skip anything the user did not touch so the request stays a
      // genuine partial update.
      if (vehicle !== null && value === original[key].trim()) continue;
      if (value === "") continue;
      values[key] = numeric.has(key) ? Number(value) : value;
    }

    onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {FIELDS.map((field) => (
        <div key={field.key}>
          <label htmlFor={field.key} className="mb-1.5 block text-sm font-medium">
            {field.label}
          </label>
          <input
            id={field.key}
            type={field.type}
            min={field.type === "number" ? 0 : undefined}
            step={field.key === "price" ? "0.01" : field.key === "quantity" ? "1" : undefined}
            value={draft[field.key]}
            onChange={(event) => setDraft({ ...draft, [field.key]: event.target.value })}
            className="w-full rounded-lg border border-forecourt-300 px-3 py-2.5 focus:border-petrol-600 focus:outline-none"
          />
          {fieldError(field.key) && (
            <p className="mt-1.5 text-sm text-tag-red">{fieldError(field.key)}</p>
          )}
        </div>
      ))}

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
        {busy ? "Saving…" : vehicle === null ? "Add vehicle" : "Save changes"}
      </button>
    </form>
  );
}
