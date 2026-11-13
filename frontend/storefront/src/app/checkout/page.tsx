"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import { fetchCart, placeOrder } from "../../lib/commerce";
import type { Cart, ShippingDetails } from "../../lib/commerce";

function price(value: string) {
  return Number(value).toFixed(2);
}

function formValue(data: FormData, key: string) {
  const value = data.get(key);
  return typeof value === "string" ? value.trim() : "";
}

export default function CheckoutPage() {
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const details: ShippingDetails = {
      contact_email: formValue(data, "contact_email"),
      recipient_name: formValue(data, "recipient_name"),
      phone_number: formValue(data, "phone_number"),
      address_line_1: formValue(data, "address_line_1"),
      address_line_2: formValue(data, "address_line_2"),
      city: formValue(data, "city"),
      region: formValue(data, "region"),
      postal_code: formValue(data, "postal_code"),
      country_code: formValue(data, "country_code").toUpperCase(),
      delivery_instructions: formValue(data, "delivery_instructions"),
    };

    try {
      const order = await placeOrder(details);
      router.push(`/orders/${order.public_id}`);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not place your order.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f6f8] px-4 py-12 text-[#142b4a]">
      <div className="mx-auto max-w-3xl">
        <Link className="text-sm font-semibold text-[#087e8b]" href="/cart">
          Back to cart
        </Link>
        <h1 className="mt-4 text-3xl font-semibold">Checkout</h1>
        {loading ? (
          <p className="mt-8 text-slate-600">Loading cart...</p>
        ) : error && !cart ? (
          <p className="mt-8 text-red-700" role="alert">{error}</p>
        ) : !cart?.items.length ? (
          <section className="mt-8 rounded-xl bg-white p-8 shadow-sm">
            <p>Your cart is empty.</p>
            <Link className="mt-5 inline-flex font-semibold text-[#087e8b]" href="/#catalog">
              Browse catalog
            </Link>
          </section>
        ) : (
          <div className="mt-8 grid gap-6 md:grid-cols-[1fr_19rem]">
            <form className="space-y-5 rounded-xl bg-white p-6 shadow-sm sm:p-8" onSubmit={handleSubmit}>
              <h2 className="text-xl font-semibold">Contact and delivery details</h2>
              <label className="block text-sm font-medium">
                Email address
                <input autoComplete="email" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="contact_email" required type="email" />
              </label>
              <label className="block text-sm font-medium">
                Recipient name
                <input autoComplete="name" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="recipient_name" required />
              </label>
              <label className="block text-sm font-medium">
                Phone number
                <input autoComplete="tel" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="phone_number" required type="tel" />
              </label>
              <label className="block text-sm font-medium">
                Address line 1
                <input autoComplete="address-line1" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="address_line_1" required />
              </label>
              <label className="block text-sm font-medium">
                Address line 2
                <input autoComplete="address-line2" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="address_line_2" />
              </label>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-medium">
                  City
                  <input autoComplete="address-level2" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="city" required />
                </label>
                <label className="block text-sm font-medium">
                  Region or state
                  <input autoComplete="address-level1" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="region" required />
                </label>
                <label className="block text-sm font-medium">
                  Postal code
                  <input autoComplete="postal-code" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="postal_code" />
                </label>
                <label className="block text-sm font-medium">
                  Country code
                  <input autoComplete="country" className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 uppercase" maxLength={2} name="country_code" placeholder="2 letters" required />
                </label>
              </div>
              <label className="block text-sm font-medium">
                Delivery instructions
                <textarea className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2" name="delivery_instructions" rows={3} />
              </label>

              {error && <p className="text-sm text-red-700" role="alert">{error}</p>}
              <button
                className="w-full rounded-md bg-[#142b4a] px-4 py-3 font-semibold text-white disabled:opacity-60"
                disabled={submitting}
                type="submit"
              >
                {submitting ? "Placing order..." : "Place order"}
              </button>
            </form>

            <aside className="h-fit rounded-xl bg-white p-6 shadow-sm">
              <h2 className="font-semibold">Order summary</h2>
              <ul className="mt-4 space-y-3 text-sm">
                {cart.items.map((item) => (
                  <li className="flex justify-between gap-3" key={item.id}>
                    <span>{item.quantity} × {item.product_name}</span>
                    <span className="font-medium">{price(item.line_total)}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-5 flex justify-between border-t border-slate-200 pt-4 font-semibold">
                <span>Items subtotal</span>
                <span>{price(cart.items_subtotal)}</span>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-500">
                Delivery fees and taxes are not included. Payment is not yet
                connected; this creates a pending order and reserves the items.
              </p>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
