/** Shapes returned by the API. Keys are camelCase, as the backend serialises them. */

export type Role = "user" | "admin";

export interface User {
  id: string;
  email: string;
  role: Role;
  createdAt: string;
}

export interface Vehicle {
  id: string;
  make: string;
  model: string;
  category: string;
  price: number;
  quantity: number;
  createdAt: string;
  updatedAt: string;
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
