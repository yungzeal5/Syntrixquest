"use client";

import Link from "next/link";
import { useState } from "react";
import type { FormEvent } from "react";

import { submitFeedback } from "../../lib/reviews";

function isFeedbackCategory(
  value: FormDataEntryValue | null,
): value is "general" | "website" | "product" | "service" {
  return (
    value === "general"
    || value === "website"
    || value === "product"
    || value === "service"
  );
}

export default function FeedbackPage() {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const name = values.get("name");
    const email = values.get("email");
    const category = values.get("category");
    const body = values.get("message");
    if (
      typeof name !== "string"
      || typeof email !== "string"
      || !isFeedbackCategory(category)
      || typeof body !== "string"
    ) {
      setError(true);
      setMessage("Complete the feedback form and try again.");
      return;
    }

    setPending(true);
    setMessage("");
    setError(false);
    try {
      await submitFeedback({
        name,
        email,
        category,
        message: body,
      });
      form.reset();
      setMessage("Thank you. Your feedback has been sent to our team.");
    } catch (submitError) {
      setError(true);
      setMessage(
        submitError instanceof Error
          ? submitError.message
          : "Could not send your feedback.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f6f8] px-4 py-12 text-[#142b4a]">
      <div className="mx-auto max-w-2xl">
        <Link className="text-sm font-semibold text-[#087e8b]" href="/">
          Syntrix Quest
        </Link>
        <section className="mt-5 rounded-xl bg-white p-6 shadow-sm sm:p-8">
          <p className="text-sm font-bold uppercase tracking-widest text-[#087e8b]">
            Customer care
          </p>
          <h1 className="mt-2 text-3xl font-semibold">Send us feedback</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Your message is private and will only be available to our support
            team. Do not include payment card details or passwords.
          </p>
          <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
            <label className="grid gap-1 text-sm font-medium">
              Topic
              <select
                className="rounded border border-slate-300 px-3 py-2"
                defaultValue="general"
                name="category"
              >
                <option value="general">General</option>
                <option value="website">Website</option>
                <option value="product">Product</option>
                <option value="service">Service</option>
              </select>
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="grid gap-1 text-sm font-medium">
                Name (optional)
                <input
                  className="rounded border border-slate-300 px-3 py-2"
                  maxLength={100}
                  name="name"
                />
              </label>
              <label className="grid gap-1 text-sm font-medium">
                Email (optional)
                <input
                  className="rounded border border-slate-300 px-3 py-2"
                  name="email"
                  type="email"
                />
              </label>
            </div>
            <label className="grid gap-1 text-sm font-medium">
              Message
              <textarea
                className="rounded border border-slate-300 px-3 py-2"
                maxLength={4000}
                name="message"
                required
                rows={6}
              />
            </label>
            {message && (
              <p
                className={`text-sm ${error ? "text-red-700" : "text-emerald-800"}`}
                role={error ? "alert" : "status"}
              >
                {message}
              </p>
            )}
            <button
              className="justify-self-start rounded-md bg-[#142b4a] px-5 py-3 font-semibold text-white disabled:opacity-60"
              disabled={pending}
              type="submit"
            >
              {pending ? "Sending..." : "Send feedback"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
