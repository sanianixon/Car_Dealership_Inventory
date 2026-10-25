/**
 * Tests for the sign-in and registration card.
 *
 * The point of interest is that the messages shown to the user are the ones the
 * server sent, not a second copy of the validation rules living in the UI.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../api";
import { AuthContext, type AuthValue } from "../auth-context";
import { AuthScreen } from "./AuthScreen";

function renderScreen(overrides: Partial<AuthValue> = {}) {
  const value: AuthValue = {
    user: null,
    initialising: false,
    isAdmin: false,
    signIn: vi.fn().mockResolvedValue(undefined),
    signUp: vi.fn().mockResolvedValue(undefined),
    signOut: vi.fn(),
    ...overrides,
  };
  render(
    <AuthContext.Provider value={value}>
      <AuthScreen />
    </AuthContext.Provider>,
  );
  return value;
}

describe("signing in", () => {
  it("passes the credentials as typed", async () => {
    const { signIn } = renderScreen();

    await userEvent.type(screen.getByLabelText(/email/i), "buyer@dealership.com");
    await userEvent.type(screen.getByLabelText(/password/i), "Passw0rd!23");
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(signIn).toHaveBeenCalledWith("buyer@dealership.com", "Passw0rd!23");
  });

  it("shows the server's message when the credentials are refused", async () => {
    renderScreen({
      signIn: vi.fn().mockRejectedValue(new ApiError("Invalid email or password", 401)),
    });

    await userEvent.type(screen.getByLabelText(/email/i), "buyer@dealership.com");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password");
  });

  it("puts a field message beside the field it belongs to", async () => {
    renderScreen({
      signIn: vi.fn().mockRejectedValue(
        new ApiError("Validation failed", 400, [
          { path: "password", message: "String should have at least 8 characters" },
        ]),
      ),
    });

    await userEvent.type(screen.getByLabelText(/email/i), "buyer@dealership.com");
    await userEvent.type(screen.getByLabelText(/password/i), "short");
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(
      await screen.findByText("String should have at least 8 characters"),
    ).toBeInTheDocument();
  });
});

describe("registering", () => {
  it("offers the admin code only on the registration tab", async () => {
    renderScreen();

    expect(screen.queryByLabelText(/admin code/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("tab", { name: /create account/i }));

    expect(screen.getByLabelText(/admin code/i)).toBeInTheDocument();
  });

  it("omits an untouched admin code rather than sending an empty one", async () => {
    const { signUp } = renderScreen();

    await userEvent.click(screen.getByRole("tab", { name: /create account/i }));
    await userEvent.type(screen.getByLabelText(/email/i), "new@dealership.com");
    await userEvent.type(screen.getByLabelText(/password/i), "Passw0rd!23");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(signUp).toHaveBeenCalledWith("new@dealership.com", "Passw0rd!23", undefined);
  });

  it("forwards an admin code when one is given", async () => {
    const { signUp } = renderScreen();

    await userEvent.click(screen.getByRole("tab", { name: /create account/i }));
    await userEvent.type(screen.getByLabelText(/email/i), "boss@dealership.com");
    await userEvent.type(screen.getByLabelText(/password/i), "Passw0rd!23");
    await userEvent.type(screen.getByLabelText(/admin code/i), "staff-code");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(signUp).toHaveBeenCalledWith(
      "boss@dealership.com",
      "Passw0rd!23",
      "staff-code",
    );
  });

  it("clears a previous error when switching tabs", async () => {
    renderScreen({
      signIn: vi.fn().mockRejectedValue(new ApiError("Invalid email or password", 401)),
    });

    await userEvent.type(screen.getByLabelText(/email/i), "buyer@dealership.com");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("tab", { name: /create account/i }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
