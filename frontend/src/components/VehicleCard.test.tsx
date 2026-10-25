/**
 * Tests for the vehicle card.
 *
 * The first one covers a requirement the brief states outright: the Purchase
 * button must be disabled when the quantity is zero.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { Vehicle } from "../types";
import { VehicleCard } from "./VehicleCard";

const BASE: Vehicle = {
  id: "v1",
  make: "Toyota",
  model: "Corolla",
  category: "Sedan",
  price: 18500,
  quantity: 4,
  createdAt: "2026-10-25T00:00:00",
  updatedAt: "2026-10-25T00:00:00",
};

function renderCard(vehicle: Partial<Vehicle> = {}, isAdmin = false) {
  const handlers = {
    onPurchase: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onRestock: vi.fn(),
  };
  render(
    <VehicleCard
      vehicle={{ ...BASE, ...vehicle }}
      isAdmin={isAdmin}
      busy={false}
      {...handlers}
    />,
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

  it("does not report a purchase when the vehicle is sold out", async () => {
    const { onPurchase } = renderCard({ quantity: 0 });

    await userEvent.click(screen.getByRole("button", { name: /out of stock/i }));

    expect(onPurchase).not.toHaveBeenCalled();
  });

  it("reports a purchase when one is made", async () => {
    const { onPurchase } = renderCard({ quantity: 3 });

    await userEvent.click(screen.getByRole("button", { name: /purchase/i }));

    expect(onPurchase).toHaveBeenCalledTimes(1);
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

it("formats the price as currency", () => {
  renderCard({ price: 18500 });

  expect(screen.getByText("$18,500")).toBeInTheDocument();
});
