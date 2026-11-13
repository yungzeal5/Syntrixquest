"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  fetchProductReviews,
  submitProductReview,
} from "../lib/reviews";
import type {
  ProductReview,
  ProductReviewSummary,
} from "../lib/reviews";

type Message = { text: string; error: boolean } | null;

function stars(rating: number) {
  return (
    <span aria-label={`${rating} out of 5 stars`} className="text-amber-600">
      {"★".repeat(rating)}
      <span className="text-slate-300">{"★".repeat(5 - rating)}</span>
    </span>
  );
}

export default function ProductReviews({
  productSlug,
}: {
  productSlug: string;
}) {
  const [summary, setSummary] = useState<ProductReviewSummary | null>(null);
  const [reviews, setReviews] = useState<ProductReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState<Message>(null);

  useEffect(() => {
    let active = true;
    fetchProductReviews(productSlug)
      .then((result) => {
        if (active) {
          setSummary(result.summary);
          setReviews(result.reviews);
          setError("");
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Could not load product reviews.",
          );
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [productSlug]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const displayName = formData.get("display_name");
    const rating = Number(formData.get("rating"));
    const title = formData.get("title");
    const body = formData.get("body");
    if (
      typeof displayName !== "string"
      || !Number.isInteger(rating)
      || rating < 1
      || rating > 5
      || typeof title !== "string"
      || typeof body !== "string"
    ) {
      setNotice({ text: "Complete the rating and review fields.", error: true });
      return;
    }

    setPending(true);
    setNotice(null);
    try {
      await submitProductReview(productSlug, {
        display_name: displayName,
        rating,
        title,
        body,
      });
      form.reset();
      setNotice({
        text: "Thanks. Your review was sent for approval before publication.",
        error: false,
      });
    } catch (submitError) {
      setNotice({
        text: submitError instanceof Error
          ? submitError.message
          : "Could not submit your review.",
        error: true,
      });
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="mt-10 border-t border-slate-200 pt-8" id="reviews">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-bold uppercase tracking-widest text-[#087e8b]">
            Customer ratings
          </p>
          <h2 className="mt-2 text-2xl font-semibold">Reviews</h2>
        </div>
        {summary && (
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-[#142b4a]">
              {summary.average_rating} / 5
            </span>
            {" · "}
            {summary.review_count} approved review
            {summary.review_count === 1 ? "" : "s"}
          </p>
        )}
      </div>

      {error && <p className="mt-4 text-sm text-red-700" role="alert">{error}</p>}
      {loading ? (
        <p className="mt-5 text-sm text-slate-600">Loading reviews...</p>
      ) : reviews.length === 0 ? (
        <p className="mt-5 text-sm text-slate-600">No approved reviews yet.</p>
      ) : (
        <ul className="mt-5 divide-y divide-slate-200">
          {reviews.map((review) => (
            <li className="py-4" key={review.id}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold">{review.display_name}</span>
                <time
                  className="text-xs text-slate-500"
                  dateTime={review.created_at}
                >
                  {new Date(review.created_at).toLocaleDateString()}
                </time>
              </div>
              <p className="mt-1">{stars(review.rating)}</p>
              {review.title && (
                <h3 className="mt-2 font-semibold">{review.title}</h3>
              )}
              <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                {review.body}
              </p>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-7 rounded-lg bg-slate-50 p-5">
        <h3 className="text-lg font-semibold">Write a review</h3>
        <p className="mt-1 text-sm text-slate-600">
          Reviews are checked by our team before they appear publicly.
        </p>
        <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
          <label className="grid gap-1 text-sm font-medium">
            Display name (optional)
            <input
              className="rounded border border-slate-300 bg-white px-3 py-2"
              maxLength={80}
              name="display_name"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Rating
            <select
              className="rounded border border-slate-300 bg-white px-3 py-2"
              defaultValue="5"
              name="rating"
              required
            >
              <option value="5">5 - Excellent</option>
              <option value="4">4 - Good</option>
              <option value="3">3 - Average</option>
              <option value="2">2 - Below average</option>
              <option value="1">1 - Poor</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium sm:col-span-2">
            Review title (optional)
            <input
              className="rounded border border-slate-300 bg-white px-3 py-2"
              maxLength={160}
              name="title"
            />
          </label>
          <label className="grid gap-1 text-sm font-medium sm:col-span-2">
            Your review
            <textarea
              className="rounded border border-slate-300 bg-white px-3 py-2"
              maxLength={3000}
              name="body"
              required
              rows={4}
            />
          </label>
          {notice && (
            <p
              className={`text-sm sm:col-span-2 ${notice.error ? "text-red-700" : "text-emerald-800"}`}
              role={notice.error ? "alert" : "status"}
            >
              {notice.text}
            </p>
          )}
          <div className="sm:col-span-2">
            <button
              className="rounded-md bg-[#142b4a] px-4 py-2 font-semibold text-white disabled:opacity-60"
              disabled={pending}
              type="submit"
            >
              {pending ? "Submitting..." : "Submit review"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
