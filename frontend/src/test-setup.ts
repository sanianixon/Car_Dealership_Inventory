/** Test environment setup, loaded by vitest before each test file. */

import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Testing Library only registers its own cleanup when a global afterEach
// exists, and this project runs vitest with globals disabled. Without this,
// every render stays in document.body and the next test finds several copies
// of the same element.
afterEach(cleanup);
