/**
 * One listing — a model the dealership stocks — as a forecourt ticket.
 *
 * It advertises the cheapest car available ("from ₹6,20,000"), how many are on
 * the lot and which colours, because that is what a model-level card can
 * honestly say. The cars themselves differ in year, owner and price, so
 * choosing one happens on the model's own page.
 *
 * The Purchase button is disabled when nothing is in stock, which the brief
 * requires. When stock exists it opens the model page to pick a specific car,
 * since "buy a Honda City" is not a complete instruction when four different
 * Citys are on the lot.
 */

import { useNavigate } from "react-router-dom";

import { formatPrice } from "../format";
import type { Vehicle } from "../types";

/** Low stock is called out so a buyer can see urgency without counting. */
function stockLabel(quantity: number): { text: string; className: string } {
  if (quantity === 0) return { text: "Sold out", className: "text-signal-out" };
  if (quantity <= 2) return { text: `Only ${quantity} left`, className: "text-signal-low" };
  return { text: `${quantity} in stock`, className: "text-ink-500" };
}

interface Props {
  vehicle: Vehicle;
  isAdmin: boolean;
  busy: boolean;
  onEdit: (vehicle: Vehicle) => void;
  onDelete: (vehicle: Vehicle) => void;
  onRestock: (vehicle: Vehicle) => void;
}

export function VehicleCard({ vehicle, isAdmin, busy, onEdit, onDelete, onRestock }: Props) {
  const navigate = useNavigate();
  const soldOut = vehicle.quantity === 0;
  const stock = stockLabel(vehicle.quantity);

  return (
    <article
      className={
        "group flex flex-col border bg-surface p-6 transition " +
        (soldOut
          ? "border-ink-100 bg-paper"
          : "border-ink-200 hover:border-ink-900 hover:shadow-[0_8px_0_-4px_rgba(20,24,27,0.08)]")
      }
    >
      <header className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-500">
          {vehicle.make}
        </p>
        <h3 className="mt-1 truncate text-xl font-bold leading-tight tracking-tight text-ink-900">
          {vehicle.model}
        </h3>
      </header>

      <div className="mb-6 mt-auto">
        {soldOut ? (
          <p className="tabular text-3xl font-extrabold leading-none tracking-tighter text-ink-300">
            —
          </p>
        ) : (
          <>
            <p className="text-[0.7rem] font-semibold uppercase tracking-[0.15em] text-ink-500">
              From
            </p>
            <p className="tabular text-4xl font-extrabold leading-none tracking-tighter text-ink-900">
              {formatPrice(vehicle.price)}
            </p>
          </>
        )}

        {vehicle.colours.length > 0 && (
          <p className="mt-3 truncate text-xs text-ink-500">
            {vehicle.colours.join(" · ")}
          </p>
        )}

        <div className="mt-3 flex items-center justify-between border-t border-ink-100 pt-3">
          <span className="text-[0.7rem] font-semibold uppercase tracking-[0.15em] text-ink-500">
            {vehicle.category}
          </span>
          <span className={"text-xs font-semibold " + stock.className}>{stock.text}</span>
        </div>
      </div>

      <button
        type="button"
        onClick={() => navigate(`/vehicles/${vehicle.id}`)}
        disabled={soldOut || busy}
        title={soldOut ? "This vehicle is out of stock" : "Choose which car to buy"}
        className={
          "w-full px-4 py-3 text-xs font-semibold uppercase tracking-widest transition " +
          (soldOut
            ? "cursor-not-allowed border border-ink-200 text-ink-300"
            : "bg-ink-900 text-paper hover:bg-clay-600 disabled:opacity-50")
        }
      >
        {soldOut ? "Out of stock" : "Purchase"}
      </button>

      {isAdmin && (
        <div className="mt-4 flex gap-4 border-t border-ink-100 pt-4 text-xs font-semibold uppercase tracking-wider">
          <button
            type="button"
            onClick={() => onEdit(vehicle)}
            className="text-ink-500 transition hover:text-ink-900"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => onRestock(vehicle)}
            className="text-ink-500 transition hover:text-ink-900"
          >
            Restock
          </button>
          <button
            type="button"
            onClick={() => onDelete(vehicle)}
            className="ml-auto text-ink-500 transition hover:text-clay-600"
          >
            Delete
          </button>
        </div>
      )}
    </article>
  );
}
