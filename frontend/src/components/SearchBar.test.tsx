/** Tests for the search controls. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EMPTY_FILTERS, type SearchFilters } from "../types";
import { SearchBar } from "./SearchBar";

function renderBar(filters: Partial<SearchFilters> = {}) {
  const props = {
    filters: { ...EMPTY_FILTERS, ...filters },
    onChange: vi.fn(),
    onSearch: vi.fn(),
    onReset: vi.fn(),
    busy: false,
  };
  render(<SearchBar {...props} />);
  return props;
}

it("reports each keystroke without losing the other filters", async () => {
  const { onChange } = renderBar({ make: "Toyota" });

  await userEvent.type(screen.getByLabelText(/^category$/i), "S");

  expect(onChange).toHaveBeenCalledWith({ ...EMPTY_FILTERS, make: "Toyota", category: "S" });
});

it("searches when the form is submitted", async () => {
  const { onSearch } = renderBar({ make: "Toyota" });

  await userEvent.click(screen.getByRole("button", { name: /search/i }));

  expect(onSearch).toHaveBeenCalledTimes(1);
});

describe("clearing", () => {
  it("offers no clear button when nothing is filtered", () => {
    renderBar();

    expect(screen.queryByRole("button", { name: /clear filters/i })).not.toBeInTheDocument();
  });

  it("offers one as soon as a filter is set", () => {
    renderBar({ category: "SUV" });

    expect(screen.getByRole("button", { name: /clear filters/i })).toBeInTheDocument();
  });

  it("treats a whitespace-only filter as no filter", () => {
    renderBar({ make: "   " });

    expect(screen.queryByRole("button", { name: /clear filters/i })).not.toBeInTheDocument();
  });

  it("resets when it is used", async () => {
    const { onReset } = renderBar({ category: "SUV" });

    await userEvent.click(screen.getByRole("button", { name: /clear filters/i }));

    expect(onReset).toHaveBeenCalledTimes(1);
  });
});

it("disables the search button while a search is running", () => {
  render(
    <SearchBar
      filters={EMPTY_FILTERS}
      onChange={vi.fn()}
      onSearch={vi.fn()}
      onReset={vi.fn()}
      busy
    />,
  );

  expect(screen.getByRole("button", { name: /searching/i })).toBeDisabled();
});
