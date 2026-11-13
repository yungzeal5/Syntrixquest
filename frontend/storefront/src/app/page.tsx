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
    <section className="catalog-section mx-auto max-w-7xl px-5 py-16 sm:py-24" id="catalog">
      <div className="catalog-heading mb-10 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="section-kicker">The essentials edit</p>
          <h2 className="mt-3 text-4xl font-semibold sm:text-5xl">Shop the catalog<span>.</span></h2>
          <p className="mt-3 max-w-xl text-base leading-7 text-slate-600">Thoughtful everyday supplies for the people who keep things moving.</p>
        </div>
        <p className="product-count">{products.length} items <span aria-hidden="true">↗</span></p>
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
              className="product-card flex flex-col"
              key={product.id}
            >
              <p className="category-label">
                {product.category.name}
              </p>
              <h3 className="mt-3 text-xl">{product.name}</h3>
              <Link
                className="product-link mt-1"
                href={`/products/${encodeURIComponent(product.slug)}`}
              >
                Product details and reviews
              </Link>
              <p className="product-description mt-3 min-h-12">
                {product.description || "A practical choice for everyday use."}
              </p>
              <div className="pack-list mt-5 border-t pt-4">
                <h4 className="pack-title">
                  Available packs
                </h4>
                <ul className="mt-3 space-y-3">
                  {product.variants.map((variant) => (
                    <li
                      className="flex items-center justify-between gap-3 text-sm"
                      key={variant.id}
                    >
                      <span>
                        <span className="variant-label block">
                          {variant.label}
                        </span>
                        <span className="variant-meta">
                          {variant.pack_quantity} {variant.pack_unit}
                        </span>
                      </span>
                      <span className="flex shrink-0 flex-col items-end gap-2">
                        <span className="variant-price">
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
      <main className="storefront min-h-screen text-[#173b35]">
      <header className="store-header">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <Link className="store-brand" href="/" aria-label="Syntrix Quest home">
            <span className="brand-mark">S</span><span>syntrix<span className="brand-dot">.</span></span>
          </Link>
          <nav aria-label="Main navigation" className="store-nav">
            <Link href="/#catalog">Shop</Link>
            <Link href="/feedback">Get in touch</Link>
            <Link className="cart-link" href="/cart">Cart <span aria-hidden="true">↗</span></Link>
          </nav>
        </div>
      </header>

      <section className="hero-section">
        <div className="hero-inner mx-auto grid max-w-7xl items-center gap-5 px-5 py-12 sm:px-8 lg:grid-cols-[.92fr_1.08fr] lg:py-16">
          <div className="hero-copy">
            <p className="hero-kicker"><span /> Supplies for everyday momentum</p>
            <h1>Good things<br />for <em>busy</em> businesses.</h1>
            <p className="hero-description">Packaging, disposables and practical essentials—selected to make your day run a little smoother.</p>
            <a className="hero-cta" href="#catalog">Explore the collection <span aria-hidden="true">↘</span></a>
            <div className="hero-note"><span className="note-star">✳</span><span>Useful by design.<br /><strong>Ready for real life.</strong></span></div>
          </div>
          <div className="hero-art" role="img" aria-label="A curated still life of packaging and business essentials">
            <div className="art-badge">THE EVERYDAY<br /><strong>COLLECTION</strong></div>
            <span className="art-caption">MADE FOR THE DAILY DO</span>
          </div>
        </div>
      </section>

      <div className="marquee-strip" aria-label="Syntrix Quest business essentials">
        <div>PACK WELL <span>✳</span> WORK SMART <span>✳</span> KEEP THINGS MOVING <span>✳</span> PACK WELL <span>✳</span> WORK SMART <span>✳</span></div>
      </div>

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

      <footer className="store-footer border-t">
        <div className="mx-auto flex max-w-7xl flex-wrap justify-between gap-3 px-5 py-7 text-sm">
          <span>Syntrix Quest</span>
          <Link className="hover:text-[#eb6846]" href="/forgot-password">
            Password help
          </Link>
          <Link className="hover:text-[#eb6846]" href="/feedback">
            Feedback
          </Link>
        </div>
      </footer>
    </main>
  );
}
