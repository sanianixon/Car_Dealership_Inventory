/**
 * One model's own page: every actual car of that model, each buyable on its own.
 *
 * This is where a purchase really happens. The dashboard card can only say
 * "from ₹6,20,000, four in stock"; which of those four you want depends on the
 * year, the colour, the owner count and the price, so the choice belongs here.
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api";
import { useAuth } from "../auth-context";
import { formatPrice } from "../format";
import type { VehicleDetail, VehicleUnit } from "../types";
import { UnitCard } from "../components/UnitCard";

export function ModelPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user, isAdmin, signOut } = useAuth();

  const [vehicle, setVehicle] = useState<VehicleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { vehicle: found } = await api.getVehicle(id);
      setVehicle(found);
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handlePurchase(unit: VehicleUnit) {
    setBusyId(unit.id);
    setError(null);
    setNotice(null);
    try {
      const { unit: bought } = await api.purchase(id, unit.id);
      setNotice(
        `Bought the ${bought.year} ${bought.colour} for ${formatPrice(bought.price)}.`,
      );
      // Re-read rather than patching state: the listing's own price and stock
      // are derived server-side and both change with the sale.
      await load();
    } catch (caught) {
      setError((caught as Error).message);
      // A refused purchase usually means someone else got there first, so show
      // the real state rather than leaving a stale card.
      await load();
    } finally {
      setBusyId(null);
    }
  }

  const available = vehicle?.units.filter((unit) => unit.isAvailable) ?? [];
  const sold = vehicle?.units.filter((unit) => !unit.isAvailable) ?? [];

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-ink-200 bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-5 sm:px-6">
          <Link
            to="/"
            className="text-sm font-extrabold uppercase tracking-[0.25em] text-ink-900"
          >
            Car Dealership
          </Link>
          <div className="ml-auto flex items-center gap-4">
            <span className="hidden text-sm text-ink-500 sm:inline">{user?.email}</span>
            {isAdmin && (
              <span className="border border-clay-600 px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-[0.15em] text-clay-700">
                Admin
              </span>
            )}
            <button
              type="button"
              onClick={signOut}
              className="border border-ink-200 px-3 py-1.5 text-sm font-semibold transition hover:bg-ink-100"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="mb-6 text-xs font-semibold uppercase tracking-widest text-ink-500 transition hover:text-ink-900"
        >
          ← Back to the forecourt
        </button>

        {loading && <p className="text-sm text-ink-500">Loading…</p>}

        {error && (
          <p
            role="alert"
            className="mb-6 border-l-2 border-clay-600 bg-clay-50 px-4 py-3 text-sm font-medium text-clay-700"
          >
            {error}
          </p>
        )}

        {notice && (
          <p className="mb-6 border-l-2 border-ink-900 bg-ink-100 px-4 py-3 text-sm font-medium">
            {notice}
          </p>
        )}

        {vehicle && (
          <>
            <div className="mb-8 border-b border-ink-200 pb-6">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-500">
                {vehicle.make}
              </p>
              <h1 className="mt-1 text-4xl font-extrabold tracking-tight sm:text-5xl">
                {vehicle.model}
              </h1>
              <p className="mt-3 text-sm text-ink-500">
                {vehicle.category} ·{" "}
                {available.length === 0
                  ? "none available"
                  : `${available.length} available from ${formatPrice(vehicle.price)}`}
              </p>
            </div>

            {available.length > 0 && (
              <section className="mb-10">
                <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-ink-500">
                  Available now
                </h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {available.map((unit) => (
                    <UnitCard
                      key={unit.id}
                      unit={unit}
                      busy={busyId === unit.id}
                      onPurchase={handlePurchase}
                    />
                  ))}
                </div>
              </section>
            )}

            {available.length === 0 && (
              <div className="mb-10 border border-dashed border-ink-200 bg-surface px-6 py-16 text-center">
                <p className="font-semibold">Every one of these has sold.</p>
                <p className="mt-1 text-sm text-ink-500">
                  Ask a member of staff when the next one is expected.
                </p>
              </div>
            )}

            {sold.length > 0 && (
              <section>
                <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-ink-500">
                  Recently sold
                </h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {sold.map((unit) => (
                    <UnitCard key={unit.id} unit={unit} busy={false} onPurchase={() => {}} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
