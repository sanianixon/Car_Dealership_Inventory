/**
 * Tests for the API client.
 *
 * These are the rules every component depends on without restating: the token
 * goes on each request, the server's error envelope becomes an ApiError that
 * forms can read field by field, and blank search filters are dropped rather
 * than sent as empty strings.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, readToken, writeToken } from "./api";

/** Build a fetch stand-in returning one response. */
function respondWith(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response);
}

/** The url and init of the first fetch call. */
function firstCall(mock: ReturnType<typeof vi.fn>) {
  const [url, init] = mock.mock.calls[0];
  return { url: url as string, init: (init ?? {}) as RequestInit };
}

beforeEach(() => {
  writeToken(null);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("authentication header", () => {
  it("sends no Authorization header when signed out", async () => {
    const fetchMock = respondWith(200, { vehicles: [] });
    vi.stubGlobal("fetch", fetchMock);

    await api.listVehicles();

    const headers = firstCall(fetchMock).init.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it("attaches the stored token as a bearer credential", async () => {
    writeToken("a-stored-token");
    const fetchMock = respondWith(200, { vehicles: [] });
    vi.stubGlobal("fetch", fetchMock);

    await api.listVehicles();

    const headers = firstCall(fetchMock).init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer a-stored-token");
  });

  it("round-trips the token through storage", () => {
    writeToken("abc");
    expect(readToken()).toBe("abc");

    writeToken(null);
    expect(readToken()).toBeNull();
  });
});

describe("error handling", () => {
  it("turns the error envelope into an ApiError carrying the status", async () => {
    vi.stubGlobal(
      "fetch",
      respondWith(409, { error: { message: "Vehicle is out of stock" } }),
    );

    await expect(api.purchase("v1")).rejects.toThrowError(ApiError);
    await expect(api.purchase("v1")).rejects.toMatchObject({
      message: "Vehicle is out of stock",
      status: 409,
    });
  });

  it("exposes per-field messages so a form can show them next to the input", async () => {
    vi.stubGlobal(
      "fetch",
      respondWith(400, {
        error: {
          message: "Validation failed",
          details: [
            { path: "price", message: "cannot be negative" },
            { path: "make", message: "must not be blank" },
          ],
        },
      }),
    );

    const caught = await api
      .createVehicle({ make: "", model: "X", category: "Y", price: -1, quantity: 1 })
      .catch((error: unknown) => error as ApiError);

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught.fieldError("price")).toBe("cannot be negative");
    expect(caught.fieldError("make")).toBe("must not be blank");
    expect(caught.fieldError("quantity")).toBeUndefined();
  });

  it("still reports a failure when the body is not the expected envelope", async () => {
    vi.stubGlobal("fetch", respondWith(500, null));

    await expect(api.listVehicles()).rejects.toMatchObject({ status: 500 });
  });
});

describe("search query", () => {
  it("drops blank and whitespace-only filters", async () => {
    const fetchMock = respondWith(200, { vehicles: [] });
    vi.stubGlobal("fetch", fetchMock);

    await api.searchVehicles({
      make: "Toyota",
      model: "",
      category: "   ",
      minPrice: "10000",
      maxPrice: "",
    });

    const { url } = firstCall(fetchMock);
    expect(url).toContain("make=Toyota");
    expect(url).toContain("minPrice=10000");
    // A blank box must widen the results, not be sent as an empty filter.
    expect(url).not.toContain("model=");
    expect(url).not.toContain("category=");
    expect(url).not.toContain("maxPrice=");
  });

  it("trims the values it does send", async () => {
    const fetchMock = respondWith(200, { vehicles: [] });
    vi.stubGlobal("fetch", fetchMock);

    await api.searchVehicles({
      make: "  Toyota  ",
      model: "",
      category: "",
      minPrice: "",
      maxPrice: "",
    });

    expect(firstCall(fetchMock).url).toContain("make=Toyota");
  });

  it("sends no query string at all when nothing is filtered", async () => {
    const fetchMock = respondWith(200, { vehicles: [] });
    vi.stubGlobal("fetch", fetchMock);

    await api.searchVehicles({
      make: "",
      model: "",
      category: "",
      minPrice: "",
      maxPrice: "",
    });

    expect(firstCall(fetchMock).url).toBe("/api/vehicles/search");
  });
});

it("treats 204 No Content as success with no body", async () => {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 204,
    json: async () => {
      throw new Error("204 responses have no body to parse");
    },
  } as unknown as Response);
  vi.stubGlobal("fetch", fetchMock);

  await expect(api.deleteVehicle("v1")).resolves.toBeUndefined();
});
