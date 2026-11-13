"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  fetchCart,
  removeCartItem,
  updateCartItem,
} from "../../lib/commerce";
import type { Cart } from "../../lib/commerce";

function price(value: string) {
  return Number(value).toFixed(2);
}

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingItem, setPendingItem] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetchCart()
      .then((result) => {
        if (active) setCart(result);
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Could not load your cart.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function changeQuantity(itemId: number, quantity: number) {
    setPendingItem(itemId);
    setError("");
    try {
      setCart(await updateCartItem(itemId, quantity));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not update your cart.",
      );
    } finally {
      setPendingItem(null);
    }
  }

  async function removeItem(itemId: number) {
    setPendingItem(itemId);
    setError("");
    try {
      setCart(await removeCartItem(itemId));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not remove this item.",
      );
    } finally {
      setPendingItem(null);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f6f8] px-4 py-12 text-[#142b4a]">
      <div className="mx-auto max-w-4xl">
        <Link className="text-sm font-semibold text-[#087e8b]" href="/">
          Syntrix Quest
        </Link>
        <h1 className="mt-4 text-3xl font-semibold">Your cart</h1>

        {loading ? (
          <p className="mt-8 text-slate-600">Loading cart...</p>
        ) : error && !cart ? (
          <p className="mt-8 text-red-700" role="alert">{error}</p>
        ) : !cart?.items.length ? (
          <section className="mt-8 rounded-xl bg-white p-8 shadow-sm">
            <p>Your cart is empty.</p>
            <Link
              className="mt-5 inline-flex rounded-md bg-[#142b4a] px-4 py-3 font-semibold text-white"
              href="/#catalog"
            >
              Browse catalog
            </Link>
          </section>
        ) : (
          <section className="mt-8 rounded-xl bg-white p-6 shadow-sm sm:p-8">
            <ul className="divide-y divide-slate-200">
              {cart.items.map((item) => (
                <li className="flex flex-wrap items-center justify-between gap-5 py-5" key={item.id}>
                  <div className="min-w-48 flex-1">
                    <h2 className="font-semibold">{item.product_name}</h2>
                    <p className="mt-1 text-sm text-slate-600">
                      {item.variant_label} · {item.pack_quantity} {item.pack_unit}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">SKU {item.sku}</p>
                    {item.quantity > item.quantity_available && (
                      <p className="mt-2 text-sm text-amber-800" role="status">
                        Only {item.quantity_available} currently available. Adjust the quantity before checkout.
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      aria-label={`Decrease ${item.product_name} quantity`}
                      className="h-9 w-9 rounded border border-slate-300 disabled:opacity-50"
                      disabled={pendingItem === item.id || item.quantity <= 1}
                      onClick={() => changeQuantity(item.id, item.quantity - 1)}
                      type="button"
                    >
                      −
                    </button>
                    <span aria-label="Quantity" className="w-8 text-center">
                      {item.quantity}
                    </span>
                    <button
                      aria-label={`Increase ${item.product_name} quantity`}
                      className="h-9 w-9 rounded border border-slate-300 disabled:opacity-50"
                      disabled={pendingItem === item.id}
                      onClick={() => changeQuantity(item.id, item.quantity + 1)}
                      type="button"
                    >
                      +
                    </button>
                  </div>
                  <div className="w-28 text-right">
                    <p className="font-semibold">{price(item.line_total)}</p>
                    <button
                      className="mt-2 text-xs font-medium text-red-700 underline"
                      disabled={pendingItem === item.id}
                      onClick={() => removeItem(item.id)}
                      type="button"
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            {error && <p className="mt-4 text-sm text-red-700" role="alert">{error}</p>}

            <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-6">
              <span className="font-semibold">Items subtotal</span>
              <span className="text-xl font-semibold">{price(cart.items_subtotal)}</span>
            </div>
            <p className="mt-2 text-right text-xs text-slate-500">
              Delivery fees and taxes are not included.
            </p>
            <div className="mt-6 flex flex-wrap justify-between gap-3">
              <Link className="rounded-md border border-slate-300 px-4 py-3 font-semibold" href="/#catalog">
                Continue shopping
              </Link>
              <Link className="rounded-md bg-[#142b4a] px-5 py-3 font-semibold text-white" href="/checkout">
                Continue to checkout
              </Link>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
