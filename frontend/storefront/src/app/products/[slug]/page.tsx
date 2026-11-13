"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Suspense } from "react";
import { useEffect, useState } from "react";

import AddToCartButton from "../../../components/add-to-cart-button";
import ProductReviews from "../../../components/product-reviews";
import { fetchCatalogProduct } from "../../../lib/catalog";
import type { CatalogProduct } from "../../../lib/catalog";

function ProductContent() {
  const params = useParams<{ slug: string }>();
  const [result, setResult] = useState<{
    slug: string;
    product: CatalogProduct | null;
    error: string;
  } | null>(null);

  useEffect(() => {
    let active = true;
    fetchCatalogProduct(params.slug)
      .then((product) => {
        if (active) {
          setResult({ slug: params.slug, product, error: "" });
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setResult({
            slug: params.slug,
            product: null,
            error: requestError instanceof Error
              ? requestError.message
              : "Could not load this product.",
          });
        }
      });
    return () => {
      active = false;
    };
  }, [params.slug]);

  const currentResult = result?.slug === params.slug ? result : null;
  if (!currentResult) {
    return (
      <main className="min-h-screen bg-[#f4f6f8] px-4 py-10 text-[#142b4a]">
        <p className="mx-auto max-w-4xl text-slate-600">Loading product...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f4f6f8] px-4 py-10 text-[#142b4a]">
      <div className="mx-auto max-w-4xl">
        <Link className="text-sm font-semibold text-[#087e8b]" href="/#catalog">
          Back to catalog
        </Link>
        {currentResult.error ? (
          <p className="mt-6 text-red-700" role="alert">
            {currentResult.error}
          </p>
        ) : !currentResult.product ? (
          <p className="mt-6 text-slate-600" role="status">
            This product could not be found.
          </p>
        ) : (
          <section className="mt-5 rounded-xl bg-white p-6 shadow-sm sm:p-8">
            <p className="text-sm font-bold uppercase tracking-widest text-[#087e8b]">
              {currentResult.product.category.name}
            </p>
            <h1 className="mt-2 text-3xl font-semibold">
              {currentResult.product.name}
            </h1>
            <p className="mt-3 leading-7 text-slate-600">
              {currentResult.product.description
                || "A practical choice for everyday use."}
            </p>
            <h2 className="mt-8 text-lg font-semibold">Available packs</h2>
            <ul className="mt-3 divide-y divide-slate-200">
              {currentResult.product.variants.map((variant) => (
                <li
                  className="flex flex-wrap items-center justify-between gap-4 py-4"
                  key={variant.id}
                >
                  <span>
                    <span className="block font-medium">{variant.label}</span>
                    <span className="text-sm text-slate-500">
                      {variant.pack_quantity} {variant.pack_unit}
                    </span>
                  </span>
                  <span className="flex items-center gap-4">
                    <span className="font-semibold">
                      {Number(variant.price).toFixed(2)}
                    </span>
                    <AddToCartButton variantId={variant.id} />
                  </span>
                </li>
              ))}
            </ul>
            <ProductReviews productSlug={currentResult.product.slug} />
          </section>
        )}
      </div>
    </main>
  );
}

export default function ProductPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#f4f6f8] px-4 py-10 text-[#142b4a]">
          <p className="mx-auto max-w-4xl text-slate-600">
            Loading product...
          </p>
        </main>
      }
    >
      <ProductContent />
    </Suspense>
  );
}
