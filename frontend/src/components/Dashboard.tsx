/**
 * The signed-in view: catalogue, search, purchasing, and stock management for
 * administrators.
 *
 * After any write the server's returned vehicle replaces the one in state,
 * rather than the UI guessing the new quantity. The server is the authority on
 * stock, and a purchase that lost a race must not leave an optimistic figure
 * on screen.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "../api";
import { useAuth } from "../auth-context";
import { EMPTY_FILTERS, type SearchFilters, type Vehicle } from "../types";
import { SearchBar } from "./SearchBar";
import { Modal } from "./Modal";
import { RestockForm } from "./RestockForm";
import { VehicleCard } from "./VehicleCard";
import { VehicleForm } from "./VehicleForm";

type Dialog =
  | { kind: "create" }
  | { kind: "edit"; vehicle: Vehicle }
  | { kind: "restock"; vehicle: Vehicle }
  | null;

export function Dashboard() {
  const { user, isAdmin, signOut } = useAuth();

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [filters, setFilters] = useState<SearchFilters>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const [busyId, setBusyId] = useState<string | null>(null);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [dialogError, setDialogError] = useState<ApiError | Error | null>(null);
  const [dialogBusy, setDialogBusy] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setListError(null);
    try {
      const { vehicles: all } = await api.listVehicles();
      setVehicles(all);
    } catch (caught) {
      setListError((caught as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  /** Swap one vehicle for the server's version of it. */
  function replace(updated: Vehicle) {
    setVehicles((current) =>
      current.map((vehicle) => (vehicle.id === updated.id ? updated : vehicle)),
    );
  }

  async function handleSearch() {
    setSearching(true);
    setListError(null);
    try {
      const { vehicles: found } = await api.searchVehicles(filters);
      setVehicles(found);
    } catch (caught) {
      setListError((caught as Error).message);
    } finally {
      setSearching(false);
    }
  }

  function handleReset() {
    setFilters(EMPTY_FILTERS);
    void loadAll();
  }

  async function handlePurchase(vehicle: Vehicle) {
    setBusyId(vehicle.id);
    setActionError(null);
    setNotice(null);
    try {
      const { vehicle: updated, purchased } = await api.purchase(vehicle.id, 1);
      replace(updated);
      setNotice(`Purchased ${purchased} × ${updated.make} ${updated.model}.`);
    } catch (caught) {
      setActionError((caught as Error).message);
      // A rejected purchase usually means someone else got there first, so
      // refresh that row to show the real stock rather than a stale number.
      try {
        const { vehicle: fresh } = await api.listVehicles().then(({ vehicles: all }) => ({
          vehicle: all.find((candidate) => candidate.id === vehicle.id),
        }));
        if (fresh) replace(fresh);
      } catch {
        // Leave the list as it is; the error message is already shown.
      }
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(vehicle: Vehicle) {
    const confirmed = window.confirm(
      `Delete ${vehicle.make} ${vehicle.model}? This cannot be undone.`,
    );
    if (!confirmed) return;

    setBusyId(vehicle.id);
    setActionError(null);
    setNotice(null);
    try {
      await api.deleteVehicle(vehicle.id);
      setVehicles((current) => current.filter((candidate) => candidate.id !== vehicle.id));
      setNotice(`Deleted ${vehicle.make} ${vehicle.model}.`);
    } catch (caught) {
      setActionError((caught as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  function openDialog(next: Dialog) {
    setDialog(next);
    setDialogError(null);
  }

  async function submitVehicle(values: Record<string, string | number>) {
    if (dialog === null) return;

    setDialogBusy(true);
    setDialogError(null);
    try {
      if (dialog.kind === "create") {
        const { vehicle: created } = await api.createVehicle(
          values as unknown as Omit<Vehicle, "id" | "createdAt" | "updatedAt">,
        );
        // Keep the list ordered by make then model, as the API returns it.
        setVehicles((current) =>
          [...current, created].sort(
            (a, b) => a.make.localeCompare(b.make) || a.model.localeCompare(b.model),
          ),
        );
        setNotice(`Added ${created.make} ${created.model}.`);
      } else if (dialog.kind === "edit") {
        const { vehicle: updated } = await api.updateVehicle(dialog.vehicle.id, values);
        replace(updated);
        setNotice(`Updated ${updated.make} ${updated.model}.`);
      }
      setDialog(null);
    } catch (caught) {
      setDialogError(caught as Error);
    } finally {
      setDialogBusy(false);
    }
  }

  async function submitRestock(quantity: number) {
    if (dialog?.kind !== "restock") return;

    setDialogBusy(true);
    setDialogError(null);
    try {
      const { vehicle: updated, restocked } = await api.restock(dialog.vehicle.id, quantity);
      replace(updated);
      setNotice(`Restocked ${updated.make} ${updated.model} by ${restocked}.`);
      setDialog(null);
    } catch (caught) {
      setDialogError(caught as Error);
    } finally {
      setDialogBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-forecourt-50">
      <header className="border-b border-forecourt-100 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-petrol-600 text-sm font-bold text-white">
              CD
            </div>
            <span className="font-bold tracking-tight">Car Dealership Inventory</span>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-sm text-forecourt-500 sm:inline">{user?.email}</span>
            {isAdmin && (
              <span className="rounded-full bg-petrol-600 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-white">
                Admin
              </span>
            )}
            <button
              type="button"
              onClick={signOut}
              className="rounded-lg border border-forecourt-300 px-3 py-1.5 text-sm font-semibold transition hover:bg-forecourt-100"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Forecourt</h1>
            <p className="mt-1 text-sm text-forecourt-500">
              {loading ? "Loading…" : `${vehicles.length} vehicles`}
            </p>
          </div>
          {isAdmin && (
            <button
              type="button"
              onClick={() => openDialog({ kind: "create" })}
              className="rounded-lg bg-petrol-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-petrol-700"
            >
              + Add vehicle
            </button>
          )}
        </div>

        <SearchBar
          filters={filters}
          onChange={setFilters}
          onSearch={handleSearch}
          onReset={handleReset}
          busy={searching}
        />

        {notice && (
          <p className="mb-4 rounded-lg bg-petrol-50 px-4 py-3 text-sm font-medium text-petrol-700">
            {notice}
          </p>
        )}
        {actionError && (
          <p role="alert" className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm font-medium text-tag-red">
            {actionError}
          </p>
        )}
        {listError && (
          <p role="alert" className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm font-medium text-tag-red">
            {listError}
          </p>
        )}

        {!loading && vehicles.length === 0 && listError === null && (
          <div className="rounded-2xl border border-dashed border-forecourt-300 bg-white px-6 py-16 text-center">
            <p className="font-semibold">No vehicles match those filters.</p>
            <p className="mt-1 text-sm text-forecourt-500">
              Try widening the search, or clear the filters to see everything.
            </p>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {vehicles.map((vehicle) => (
            <VehicleCard
              key={vehicle.id}
              vehicle={vehicle}
              isAdmin={isAdmin}
              busy={busyId === vehicle.id}
              onPurchase={handlePurchase}
              onEdit={(target) => openDialog({ kind: "edit", vehicle: target })}
              onRestock={(target) => openDialog({ kind: "restock", vehicle: target })}
              onDelete={handleDelete}
            />
          ))}
        </div>
      </main>

      {dialog?.kind === "create" && (
        <Modal title="Add vehicle" onClose={() => setDialog(null)}>
          <VehicleForm
            vehicle={null}
            error={dialogError}
            busy={dialogBusy}
            onSubmit={submitVehicle}
          />
        </Modal>
      )}

      {dialog?.kind === "edit" && (
        <Modal title={`Edit ${dialog.vehicle.make} ${dialog.vehicle.model}`} onClose={() => setDialog(null)}>
          <VehicleForm
            vehicle={dialog.vehicle}
            error={dialogError}
            busy={dialogBusy}
            onSubmit={submitVehicle}
          />
        </Modal>
      )}

      {dialog?.kind === "restock" && (
        <Modal title="Restock" onClose={() => setDialog(null)}>
          <RestockForm
            vehicle={dialog.vehicle}
            error={dialogError}
            busy={dialogBusy}
            onSubmit={submitRestock}
          />
        </Modal>
      )}
    </div>
  );
}
