/** Shapes returned by the API. Keys are camelCase, as the backend serialises them. */

export type Role = "user" | "admin";

export interface User {
  id: string;
  email: string;
  role: Role;
  createdAt: string;
}

/**
 * A listing: a model the dealership stocks, such as "Honda City".
 *
 * It has no year, colour or history of its own — those belong to the
 * individual cars. Its price and quantity are derived by the server from the
 * cars still available, so a card can never advertise stock the lot has sold.
 */
export interface Vehicle {
  id: string;
  make: string;
  model: string;
  category: string;
  /** Rupees. The cheapest car currently available, or 0 when sold out. */
  price: number;
  /** How many cars of this model are still for sale. */
  quantity: number;
  /** The distinct colours actually on the lot. */
  colours: string[];
  createdAt: string;
  updatedAt: string;
}

/** One physical car, with its own history and its own price. */
export interface VehicleUnit {
  id: string;
  year: number;
  colour: string;
  /** Rupees. Each car is priced on its own condition and history. */
  price: number;
  /** 1 means first owner, as used-car listings count it. */
  ownershipNumber: number;
  /** ISO date the dealership took this car in. */
  acquiredOn: string;
  isAvailable: boolean;
}

/** A listing together with the cars behind it. */
export interface VehicleDetail extends Vehicle {
  units: VehicleUnit[];
}

/** One car being taken onto the lot. */
export interface UnitDraft {
  year: number;
  colour: string;
  price: number;
  ownershipNumber: number;
  acquiredOn: string;
}

/** Filters for the search endpoint. Blank values are dropped before sending. */
export interface SearchFilters {
  make: string;
  model: string;
  category: string;
  minPrice: string;
  maxPrice: string;
}

/** The "nothing selected" filter set, used to initialise and to clear the form. */
export const EMPTY_FILTERS: SearchFilters = {
  make: "",
  model: "",
  category: "",
  minPrice: "",
  maxPrice: "",
};
