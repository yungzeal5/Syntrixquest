"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import { postPasswordReset } from "../../lib/password-reset";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    setIsSubmitting(true);

    try {
      const response = await postPasswordReset("password-reset/", { email });
      setMessage(
        typeof response.detail === "string"
          ? response.detail
          : "If an account with that email exists, reset instructions will be sent.",
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not contact the account service. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f6f8] px-4 py-16 text-[#142b4a]">
      <section className="mx-auto max-w-md rounded-xl bg-white p-8 shadow-sm">
        <p className="text-sm font-bold uppercase tracking-widest text-[#087e8b]">
          Syntrix Quest
        </p>
        <h1 className="mt-3 text-3xl font-semibold">Reset your password</h1>
        <p className="mt-3 text-sm text-slate-600">
          Enter the email address on your account. If it is registered, we will
          send password-reset instructions.
        </p>

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="email">
              Email address
            </label>
            <input
              autoComplete="email"
              className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-[#087e8b] focus:ring-2 focus:ring-[#087e8b]/20"
              id="email"
              name="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </div>

          <button
            className="w-full rounded-md bg-[#142b4a] px-4 py-3 font-semibold text-white hover:bg-[#1d3b63] disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Sending..." : "Send reset instructions"}
          </button>
        </form>

        {message && (
          <p className="mt-5 text-sm text-emerald-800" role="status">
            {message}
          </p>
        )}
        {error && (
          <p className="mt-5 text-sm text-red-700" role="alert">
            {error}
          </p>
        )}
      </section>
    </main>
  );
}
