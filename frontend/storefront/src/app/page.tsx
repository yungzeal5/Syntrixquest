import Link from "next/link";
import { Suspense } from "react";

import { fetchCatalog } from "../lib/catalog";
import type { CatalogProduct } from "../lib/catalog";
import AddToCartButton from "../components/add-to-cart-button";

function formatPrice(price: string) {
  return Number(price).toFixed(2);
}

async function CatalogSection() {
  let products: CatalogProduct[] = [];
  let catalogError = "";

  try {
    products = await fetchCatalog();
  } catch (error) {
    catalogError =
      error instanceof Error
        ? error.message
        : "The catalog could not be loaded.";
  }

  return (
    <section
      className="mx-auto max-w-7xl px-5 py-14 sm:py-18"
      id="catalog"
    >
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-bold uppercase tracking-widest text-[#087e8b]">
            Syntrix selection
          </p>
          <h2 className="mt-2 text-3xl font-semibold">Shop the catalog</h2>
        </div>
        <p className="text-sm text-slate-500">
          {products.length} product{products.length === 1 ? "" : "s"}
        </p>
      </div>

      {catalogError ? (
        <div
          className="rounded-lg border border-red-200 bg-red-50 p-5 text-red-800"
          role="alert"
        >
          <h3 className="font-semibold">Catalog unavailable</h3>
          <p className="mt-1 text-sm">
            {catalogError} Check that the backend is running and try again.
          </p>
        </div>
      ) : products.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
          <h3 className="text-lg font-semibold">No products yet</h3>
          <p className="mt-2 text-sm text-slate-600">
            Products will appear here once they are added to the catalog.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <article
              className="flex flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
              key={product.id}
            >
              <p className="text-xs font-bold uppercase tracking-widest text-[#087e8b]">
                {product.category.name}
              </p>
              <h3 className="mt-3 text-xl font-semibold">{product.name}</h3>
              <Link
                className="mt-1 text-sm font-semibold text-[#087e8b] hover:underline"
                href={`/products/${encodeURIComponent(product.slug)}`}
              >
                Product details and reviews
              </Link>
              <p className="mt-2 min-h-12 text-sm leading-6 text-slate-600">
                {product.description || "A practical choice for everyday use."}
              </p>
              <div className="mt-5 border-t border-slate-100 pt-4">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Available packs
                </h4>
                <ul className="mt-3 space-y-3">
                  {product.variants.map((variant) => (
                    <li
                      className="flex items-center justify-between gap-3 text-sm"
                      key={variant.id}
                    >
                      <span>
                        <span className="block font-medium text-slate-800">
                          {variant.label}
                        </span>
                        <span className="text-xs text-slate-500">
                          {variant.pack_quantity} {variant.pack_unit}
                        </span>
                      </span>
                      <span className="flex shrink-0 flex-col items-end gap-2">
                        <span className="font-semibold">
                          {formatPrice(variant.price)}
                        </span>
                        <AddToCartButton variantId={variant.id} />
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f4f6f8] text-[#142b4a]">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5">
          <Link className="text-xl font-bold tracking-tight" href="/">
            Syntrix <span className="text-[#087e8b]">Quest</span>
          </Link>
          <nav aria-label="Main navigation">
            <div className="flex items-center gap-5">
              <Link
                className="text-sm font-semibold text-slate-600 hover:text-[#087e8b]"
                href="/cart"
              >
                Cart
              </Link>
              <Link
                className="text-sm font-semibold text-slate-600 hover:text-[#087e8b]"
                href="/forgot-password"
              >
                Account help
              </Link>
              <Link
                className="text-sm font-semibold text-slate-600 hover:text-[#087e8b]"
                href="/feedback"
              >
                Feedback
              </Link>
            </div>
          </nav>
        </div>
      </header>

      <section className="bg-[#142b4a] text-white">
        <div className="mx-auto max-w-7xl px-5 py-16 sm:py-24">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-teal-300">
            Packaging, disposables & business supplies
          </p>
          <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-tight sm:text-6xl">
            Everyday essentials, ready for your business.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-200">
            Browse practical supplies for work, retail, food service, and home.
          </p>
          <a
            className="mt-8 inline-flex rounded-md bg-teal-300 px-5 py-3 font-semibold text-[#142b4a] hover:bg-teal-200"
            href="#catalog"
          >
            Browse catalog
          </a>
        </div>
      </section>

      <Suspense
        fallback={
          <section
            className="mx-auto max-w-7xl px-5 py-14"
            id="catalog"
          >
            <p className="text-slate-600">Loading catalog...</p>
          </section>
        }
      >
        <CatalogSection />
      </Suspense>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap justify-between gap-3 px-5 py-6 text-sm text-slate-500">
          <span>Syntrix Quest</span>
          <Link className="hover:text-[#087e8b]" href="/forgot-password">
            Password help
          </Link>
          <Link className="hover:text-[#087e8b]" href="/feedback">
            Feedback
          </Link>
        </div>
      </footer>
    </main>
  );
}
