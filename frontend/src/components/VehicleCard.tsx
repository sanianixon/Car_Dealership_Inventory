/**
 * One vehicle, presented as a forecourt hang-tag.
 *
 * The Purchase button is disabled when nothing is in stock, which the brief
 * requires. It is also made obvious: a greyed-out button alone leaves people
 * clicking at it, so the card is dimmed and the stock line says "Sold out".
 */

import type { Vehicle } from "../types";

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

/** Low stock is called out so a buyer can see urgency without counting. */
function stockLabel(quantity: number): { text: string; className: string } {
  if (quantity === 0) return { text: "Sold out", className: "text-tag-red" };
  if (quantity <= 2)
    return { text: `Only ${quantity} left`, className: "text-tag-amber" };
  return { text: `${quantity} in stock`, className: "text-forecourt-500" };
}

interface Props {
  vehicle: Vehicle;
  isAdmin: boolean;
  busy: boolean;
  onPurchase: (vehicle: Vehicle) => void;
  onEdit: (vehicle: Vehicle) => void;
  onDelete: (vehicle: Vehicle) => void;
  onRestock: (vehicle: Vehicle) => void;
}

export function VehicleCard({
  vehicle,
  isAdmin,
  busy,
  onPurchase,
  onEdit,
  onDelete,
  onRestock,
}: Props) {
  const soldOut = vehicle.quantity === 0;
  const stock = stockLabel(vehicle.quantity);

  return (
    <article
      className={
        "flex flex-col rounded-2xl border bg-white p-5 shadow-sm transition " +
        (soldOut
          ? "border-forecourt-100 opacity-75"
          : "border-forecourt-100 hover:border-petrol-200 hover:shadow-md")
      }
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-lg font-bold leading-tight text-forecourt-900">
            {vehicle.make} {vehicle.model}
          </h3>
          <span className="mt-1.5 inline-block rounded-full bg-petrol-50 px-2.5 py-0.5 text-xs font-semibold text-petrol-700">
            {vehicle.category}
          </span>
        </div>
        {/* The punched hole of a hang-tag. Decorative only. */}
        <div
          aria-hidden="true"
          className="mt-1 h-3 w-3 shrink-0 rounded-full border-2 border-forecourt-300"
        />
      </div>

      <div className="mb-4 mt-auto">
        <p className="text-2xl font-bold tracking-tight text-forecourt-900">
          {money.format(vehicle.price)}
        </p>
        <p className={"mt-1 text-sm font-medium " + stock.className}>{stock.text}</p>
      </div>

      <button
        type="button"
        onClick={() => onPurchase(vehicle)}
        disabled={soldOut || busy}
        title={soldOut ? "This vehicle is out of stock" : undefined}
        className={
          "w-full rounded-lg px-4 py-2.5 font-semibold transition " +
          (soldOut
            ? "cursor-not-allowed bg-forecourt-100 text-forecourt-500"
            : "bg-petrol-600 text-white hover:bg-petrol-700 disabled:opacity-60")
        }
      >
        {soldOut ? "Out of stock" : busy ? "Working…" : "Purchase"}
      </button>

      {isAdmin && (
        <div className="mt-3 flex gap-2 border-t border-forecourt-100 pt-3">
          <button
            type="button"
            onClick={() => onEdit(vehicle)}
            className="flex-1 rounded-md px-2 py-1.5 text-sm font-medium text-forecourt-700 transition hover:bg-forecourt-100"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => onRestock(vehicle)}
            className="flex-1 rounded-md px-2 py-1.5 text-sm font-medium text-petrol-700 transition hover:bg-petrol-50"
          >
            Restock
          </button>
          <button
            type="button"
            onClick={() => onDelete(vehicle)}
            className="flex-1 rounded-md px-2 py-1.5 text-sm font-medium text-tag-red transition hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      )}
    </article>
  );
}
