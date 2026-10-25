/**
 * Add or edit a listing. Admin only.
 *
 * Creating a listing means listing a model *and* the first car of it, because
 * a model with no cars would show as sold out the moment it existed. Further
 * cars are taken in through Restock.
 *
 * Editing touches only the listing's own fields. A car's year, colour, price
 * or history is not editable here: it describes that car, not the model.
 */

import { useState, type FormEvent } from "react";

import { ApiError } from "../api";
import type { UnitDraft, Vehicle } from "../types";

const FIELD =
  "w-full border border-ink-200 bg-surface px-3 py-2.5 text-ink-900 " +
  "placeholder:text-ink-300 focus:border-clay-600 focus:outline-none";
const LABEL = "mb-1 block text-xs font-semibold uppercase tracking-widest text-ink-500";

interface Props {
  /** null means "list a new model". */
  vehicle: Vehicle | null;
  error: ApiError | Error | null;
  busy: boolean;
  onSubmit: (values: Record<string, unknown>) => void;
}

export function VehicleForm({ vehicle, error, busy, onSubmit }: Props) {
  const creating = vehicle === null;

  const [make, setMake] = useState(vehicle?.make ?? "");
  const [model, setModel] = useState(vehicle?.model ?? "");
  const [category, setCategory] = useState(vehicle?.category ?? "");

  const [year, setYear] = useState("");
  const [colour, setColour] = useState("");
  const [price, setPrice] = useState("");
  const [owners, setOwners] = useState("1");
  const [acquiredOn, setAcquiredOn] = useState(new Date().toISOString().slice(0, 10));

  const fieldError = (path: string) =>
    error instanceof ApiError
      ? // The server reports a car's field as "units.0.price"; show it against
        // the input the admin actually typed into.
        error.fieldError(path) ?? error.fieldError(`units.0.${path}`)
      : undefined;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (creating) {
      const unit: UnitDraft = {
        year: Number(year),
        colour: colour.trim(),
        price: Number(price),
        ownershipNumber: Number(owners),
        acquiredOn,
      };
      onSubmit({ make: make.trim(), model: model.trim(), category: category.trim(), units: [unit] });
      return;
    }

    // On edit, send only what actually changed so the request stays a genuine
    // partial update and an untouched field cannot be clobbered.
    const changes: Record<string, unknown> = {};
    if (make.trim() !== vehicle.make) changes.make = make.trim();
    if (model.trim() !== vehicle.model) changes.model = model.trim();
    if (category.trim() !== vehicle.category) changes.category = category.trim();
    onSubmit(changes);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="make" className={LABEL}>
          Make
        </label>
        <input id="make" value={make} onChange={(e) => setMake(e.target.value)} className={FIELD} />
        {fieldError("make") && <p className="mt-1.5 text-sm text-clay-700">{fieldError("make")}</p>}
      </div>

      <div>
        <label htmlFor="model" className={LABEL}>
          Model
        </label>
        <input id="model" value={model} onChange={(e) => setModel(e.target.value)} className={FIELD} />
        {fieldError("model") && (
          <p className="mt-1.5 text-sm text-clay-700">{fieldError("model")}</p>
        )}
      </div>

      <div>
        <label htmlFor="category" className={LABEL}>
          Category
        </label>
        <input
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className={FIELD}
        />
        {fieldError("category") && (
          <p className="mt-1.5 text-sm text-clay-700">{fieldError("category")}</p>
        )}
      </div>

      {creating && (
        <fieldset className="space-y-4 border-t border-ink-100 pt-4">
          <legend className="text-xs font-semibold uppercase tracking-widest text-ink-500">
            The first car of this model
          </legend>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="year" className={LABEL}>
                Build year
              </label>
              <input
                id="year"
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
              <label htmlFor="colour" className={LABEL}>
                Colour
              </label>
              <input
                id="colour"
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
            <label htmlFor="price" className={LABEL}>
              Price (₹)
            </label>
            <input
              id="price"
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
              <label htmlFor="owners" className={LABEL}>
                Ownership number
              </label>
              <input
                id="owners"
                type="number"
                min="1"
                value={owners}
                onChange={(e) => setOwners(e.target.value)}
                className={FIELD}
              />
              <p className="mt-1.5 text-xs text-ink-500">1 is the first owner</p>
            </div>
            <div>
              <label htmlFor="acquiredOn" className={LABEL}>
                Date acquired
              </label>
              <input
                id="acquiredOn"
                type="date"
                value={acquiredOn}
                onChange={(e) => setAcquiredOn(e.target.value)}
                className={FIELD}
              />
            </div>
          </div>
        </fieldset>
      )}

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
        {busy ? "Saving…" : creating ? "List this model" : "Save changes"}
      </button>
    </form>
  );
}
