/**
 * Tests for the listing card.
 *
 * The first one covers a requirement the brief states outright: the Purchase
 * button must be disabled when the quantity is zero.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import type { Vehicle } from "../types";
import { VehicleCard } from "./VehicleCard";

const BASE: Vehicle = {
  id: "v1",
  make: "Hyundai",
  model: "Creta",
  category: "SUV",
  price: 1520000,
  quantity: 3,
  colours: ["Abyss Black", "Polar White"],
  createdAt: "2026-10-25T00:00:00",
  updatedAt: "2026-10-25T00:00:00",
};

/** Renders the card inside a router, and reports where navigation lands. */
function renderCard(vehicle: Partial<Vehicle> = {}, isAdmin = false) {
  const handlers = { onEdit: vi.fn(), onDelete: vi.fn(), onRestock: vi.fn() };
  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route
          path="/"
          element={
            <VehicleCard
              vehicle={{ ...BASE, ...vehicle }}
              isAdmin={isAdmin}
              busy={false}
              {...handlers}
            />
          }
        />
        <Route path="/vehicles/:id" element={<p>model page for {vehicle.id ?? BASE.id}</p>} />
      </Routes>
    </MemoryRouter>,
  );
  return handlers;
}

describe("stock state", () => {
  it("disables the purchase button when nothing is in stock", () => {
    renderCard({ quantity: 0 });

    expect(screen.getByRole("button", { name: /out of stock/i })).toBeDisabled();
  });

  it("allows purchasing while stock remains", () => {
    renderCard({ quantity: 1 });

    expect(screen.getByRole("button", { name: /purchase/i })).toBeEnabled();
  });

  it("opens the model page so a buyer can choose which car", async () => {
    renderCard();

    await userEvent.click(screen.getByRole("button", { name: /purchase/i }));

    // "Buy a Creta" is not a complete instruction when three different Cretas
    // are on the lot, so the card hands over to the model's own page.
    expect(screen.getByText(/model page for v1/)).toBeInTheDocument();
  });

  it("goes nowhere when the model is sold out", async () => {
    renderCard({ quantity: 0 });

    await userEvent.click(screen.getByRole("button", { name: /out of stock/i }));

    expect(screen.queryByText(/model page/)).not.toBeInTheDocument();
  });

  it("says sold out rather than showing a count of zero", () => {
    renderCard({ quantity: 0 });

    expect(screen.getByText("Sold out")).toBeInTheDocument();
  });

  it("warns when stock is nearly gone", () => {
    renderCard({ quantity: 2 });

    expect(screen.getByText("Only 2 left")).toBeInTheDocument();
  });

  it("shows a plain count when there is plenty", () => {
    renderCard({ quantity: 7 });

    expect(screen.getByText("7 in stock")).toBeInTheDocument();
  });

  it("hides the price entirely when nothing is available", () => {
    renderCard({ quantity: 0, price: 0, colours: [] });

    expect(screen.queryByText(/₹/)).not.toBeInTheDocument();
  });
});

describe("what a listing can honestly advertise", () => {
  it("quotes the cheapest car as a from-price", () => {
    renderCard({ price: 1520000 });

    expect(screen.getByText("From")).toBeInTheDocument();
    // Indian digit grouping: not ₹1,520,000.
    expect(screen.getByText("₹15,20,000")).toBeInTheDocument();
  });

  it("lists the colours actually on the lot", () => {
    renderCard({ colours: ["Abyss Black", "Polar White"] });

    expect(screen.getByText("Abyss Black · Polar White")).toBeInTheDocument();
  });
});

describe("admin controls", () => {
  it("hides them from an ordinary buyer", () => {
    renderCard({}, false);

    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /restock/i })).not.toBeInTheDocument();
  });

  it("offers edit, restock and delete to an administrator", () => {
    renderCard({}, true);

    expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /restock/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
  });

  it("still disables purchasing for an admin when stock is zero", () => {
    renderCard({ quantity: 0 }, true);

    expect(screen.getByRole("button", { name: /out of stock/i })).toBeDisabled();
  });
});
