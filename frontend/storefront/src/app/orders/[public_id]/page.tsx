"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { cancelOrder, fetchOrder } from "../../../lib/commerce";
import type { Order } from "../../../lib/commerce";

function price(value: string) {
  return Number(value).toFixed(2);
}

function OrderContent() {
  const params = useParams<{ public_id: string }>();
  const publicId = params.public_id;
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    fetchOrder(publicId)
      .then((result) => {
        if (active) setOrder(result);
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Could not load this order.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [publicId]);

  async function handleCancel() {
    if (!order) return;
    setPending(true);
    setError("");
    try {
      setOrder(await cancelOrder(order.public_id));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not cancel this order.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f6f8] px-4 py-12 text-[#142b4a]">
      <div className="mx-auto max-w-3xl">
        <Link className="text-sm font-semibold text-[#087e8b]" href="/">
          Syntrix Quest
        </Link>
        <h1 className="mt-4 text-3xl font-semibold">Order details</h1>
        {loading ? (
          <p className="mt-8 text-slate-600">Loading order...</p>
        ) : error && !order ? (
          <p className="mt-8 text-red-700" role="alert">{error}</p>
        ) : order ? (
          <section className="mt-8 rounded-xl bg-white p-6 shadow-sm sm:p-8">
            <p className="break-all text-sm text-slate-500">
              Order {order.public_id}
            </p>
            <h2 className="mt-2 text-xl font-semibold">
              {order.status === "pending_payment"
                ? "Pending payment"
                : order.status === "paid"
                  ? "Paid"
                  : "Cancelled"}
            </h2>
            {order.status === "pending_payment" && (
              <p className="mt-2 text-sm text-amber-800">
                Payment is not connected yet. Your items are reserved until
                payment is integrated or you cancel this order.
              </p>
            )}
            <ul className="mt-6 divide-y divide-slate-200">
              {order.items.map((item) => (
                <li className="flex justify-between gap-4 py-4" key={item.sku}>
                  <span>
                    <span className="block font-medium">
                      {item.product_name} — {item.variant_label}
                    </span>
                    <span className="text-sm text-slate-500">
                      {item.quantity} × {price(item.unit_price)}
                    </span>
                  </span>
                  <span className="font-semibold">{price(item.line_total)}</span>
                </li>
              ))}
            </ul>
            <div className="flex justify-between border-t border-slate-200 pt-5 font-semibold">
              <span>Items subtotal</span>
              <span>{price(order.items_subtotal)}</span>
            </div>
            <div className="mt-6 border-t border-slate-100 pt-5 text-sm text-slate-600">
              <h3 className="font-semibold text-[#142b4a]">Delivery address</h3>
              <p className="mt-2">{order.recipient_name} · {order.phone_number}</p>
              <p>
                {order.address_line_1}
                {order.address_line_2 ? `, ${order.address_line_2}` : ""}
              </p>
              <p>{order.city}, {order.region} {order.postal_code}</p>
              <p>{order.country_code}</p>
              <p>{order.contact_email}</p>
            </div>
            {error && <p className="mt-5 text-sm text-red-700" role="alert">{error}</p>}
            <div className="mt-6 flex flex-wrap gap-3">
              {order.status === "pending_payment" && (
                <button
                  className="rounded-md border border-red-300 px-4 py-3 font-semibold text-red-700 disabled:opacity-60"
                  disabled={pending}
                  onClick={handleCancel}
                  type="button"
                >
                  {pending ? "Cancelling..." : "Cancel order"}
                </button>
              )}
              <Link
                className="rounded-md bg-[#142b4a] px-4 py-3 font-semibold text-white"
                href="/#catalog"
              >
                Continue shopping
              </Link>
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}

export default function OrderPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#f4f6f8] px-4 py-12 text-[#142b4a]">
          <p className="mx-auto max-w-3xl text-slate-600">Loading order...</p>
        </main>
      }
    >
      <OrderContent />
    </Suspense>
  );
}
