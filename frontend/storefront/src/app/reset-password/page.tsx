"use client";

import { Suspense, useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "next/navigation";

import { postPasswordReset } from "../../lib/password-reset";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const uid = searchParams.get("uid");
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!uid || !token) {
      setError("This password-reset link is invalid or has expired.");
      return;
    }

    setMessage("");
    setError("");
    setIsSubmitting(true);

    try {
      const response = await postPasswordReset("password-reset/confirm/", {
        uid,
        token,
        new_password: password,
        new_password_confirm: passwordConfirm,
      });
      setMessage(
        typeof response.detail === "string"
          ? response.detail
          : "Your password has been reset.",
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

  if (!uid || !token) {
    return (
      <section className="mx-auto max-w-md rounded-xl bg-white p-8 shadow-sm">
        <p className="text-sm font-bold uppercase tracking-widest text-[#087e8b]">
          Syntrix Quest
        </p>
        <h1 className="mt-3 text-3xl font-semibold">Invalid reset link</h1>
        <p className="mt-3 text-sm text-slate-600">
          Request a new password-reset email to continue.
        </p>
        <a
          className="mt-6 inline-block font-semibold text-[#087e8b] underline"
          href="/forgot-password"
        >
          Request another reset link
        </a>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-md rounded-xl bg-white p-8 shadow-sm">
      <p className="text-sm font-bold uppercase tracking-widest text-[#087e8b]">
        Syntrix Quest
      </p>
      <h1 className="mt-3 text-3xl font-semibold">Choose a new password</h1>

      <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
        <div>
          <label className="mb-2 block text-sm font-medium" htmlFor="password">
            New password
          </label>
          <input
            autoComplete="new-password"
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-[#087e8b] focus:ring-2 focus:ring-[#087e8b]/20"
            id="password"
            minLength={8}
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium"
            htmlFor="password-confirm"
          >
            Confirm new password
          </label>
          <input
            autoComplete="new-password"
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-[#087e8b] focus:ring-2 focus:ring-[#087e8b]/20"
            id="password-confirm"
            minLength={8}
            onChange={(event) => setPasswordConfirm(event.target.value)}
            required
            type="password"
            value={passwordConfirm}
          />
        </div>

        <button
          className="w-full rounded-md bg-[#142b4a] px-4 py-3 font-semibold text-white hover:bg-[#1d3b63] disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? "Updating..." : "Update password"}
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
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="min-h-screen bg-[#f4f6f8] px-4 py-16 text-[#142b4a]">
      <Suspense
        fallback={
          <p className="mx-auto max-w-md text-center text-slate-600">
            Loading password reset...
          </p>
        }
      >
        <ResetPasswordForm />
      </Suspense>
    </main>
  );
}
