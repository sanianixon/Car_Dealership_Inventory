/**
 * A small accessible dialog: backdrop click and Escape both close it, and
 * focus is moved into the panel when it opens.
 */

import { useEffect, useRef, type ReactNode } from "react";

interface Props {
  title: string;
  onClose: () => void;
  children: ReactNode;
}

export function Modal({ title, onClose, children }: Props) {
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    panel.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-forecourt-900/40 p-4 sm:items-center"
      onClick={onClose}
    >
      <div
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        // Stop a click inside the panel from reaching the backdrop handler.
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl focus:outline-none"
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-bold text-forecourt-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-md px-2 py-1 text-xl leading-none text-forecourt-500 transition hover:bg-forecourt-100"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
