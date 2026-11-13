"use client";

import { useState } from "react";

import { addCartItem } from "../lib/commerce";

export default function AddToCartButton({ variantId }: { variantId: number }) {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");

  async function handleAdd() {
    setPending(true);
    setMessage("");
    try {
      await addCartItem(variantId);
      setMessage("Added to cart.");
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not add this item.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <span className="flex flex-col items-end gap-1">
      <button
        className="rounded-md bg-[#142b4a] px-3 py-2 text-xs font-semibold text-white hover:bg-[#1d3b63] disabled:opacity-60"
        disabled={pending}
        onClick={handleAdd}
        type="button"
      >
        {pending ? "Adding..." : "Add to cart"}
      </button>
      {message && (
        <span aria-live="polite" className="max-w-40 text-right text-xs text-slate-600">
          {message}
        </span>
      )}
    </span>
  );
}
