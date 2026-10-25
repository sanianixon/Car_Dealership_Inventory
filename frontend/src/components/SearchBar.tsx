/**
 * Filter controls for the catalogue.
 *
 * Blank fields are dropped by the API client, so leaving a box empty widens
 * the results rather than matching nothing.
 */

import type { FormEvent } from "react";

import type { SearchFilters } from "../types";

interface Props {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onSearch: () => void;
  onReset: () => void;
  busy: boolean;
}

const FIELDS: { key: keyof SearchFilters; label: string; type: string; placeholder: string }[] = [
  { key: "make", label: "Make", type: "text", placeholder: "Toyota" },
  { key: "model", label: "Model", type: "text", placeholder: "Corolla" },
  { key: "category", label: "Category", type: "text", placeholder: "SUV" },
  { key: "minPrice", label: "Min price", type: "number", placeholder: "10000" },
  { key: "maxPrice", label: "Max price", type: "number", placeholder: "40000" },
];

export function SearchBar({ filters, onChange, onSearch, onReset, busy }: Props) {
  const isFiltered = Object.values(filters).some((value) => value.trim() !== "");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSearch();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-8 border border-ink-100 bg-surface p-4 shadow-sm sm:p-5"
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {FIELDS.map((field) => (
          <div key={field.key}>
            <label
              htmlFor={field.key}
              className="mb-1 block text-xs font-semibold uppercase tracking-wide text-ink-500"
            >
              {field.label}
            </label>
            <input
              id={field.key}
              type={field.type}
              min={field.type === "number" ? 0 : undefined}
              value={filters[field.key]}
              placeholder={field.placeholder}
              onChange={(event) => onChange({ ...filters, [field.key]: event.target.value })}
              className="w-full border border-ink-200 px-3 py-2 text-sm focus:border-clay-600 focus:outline-none"
            />
          </div>
        ))}
      </div>

      <div className="mt-4 flex gap-2">
        <button
          type="submit"
          disabled={busy}
          className="bg-ink-900 px-5 py-2 text-sm font-semibold text-paper transition hover:bg-ink-700 disabled:opacity-60"
        >
          {busy ? "Searching…" : "Search"}
        </button>
        {isFiltered && (
          <button
            type="button"
            onClick={onReset}
            className="px-4 py-2 text-sm font-semibold text-ink-700 transition hover:bg-ink-100"
          >
            Clear filters
          </button>
        )}
      </div>
    </form>
  );
}
