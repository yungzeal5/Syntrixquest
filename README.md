# Syntrix Quest

An e-commerce platform for a packaging, disposable products, and business
supplies retailer.

## Repository layout

```text
frontend/storefront/  Next.js customer storefront
frontend/admin/       React + Vite administration dashboard
backend/              Django REST API modular monolith
docs/                 Engineering decisions and future specifications
infrastructure/       Deployment assets when deployment is planned
```

## First-time setup

1. Copy `backend/.env.example` to `backend/.env` and replace the development secret before sharing the environment.
2. Install backend packages: `python -m pip install -r backend/requirements.txt`.
3. Install frontend packages from the repository root: `npm install`.
4. Copy the frontend `.env.example` files if their API defaults need changing.
5. Apply migrations: `python backend/manage.py migrate`.
6. Create the initial staff role groups: `python backend/manage.py sync_staff_roles`.

## Run locally

Open three terminals from the repository root:

```powershell
python backend/manage.py runserver
npm run dev:storefront
npm run dev:admin
```

The API health check is `http://localhost:8000/api/v1/health/`. The storefront runs at `http://localhost:3000`; the admin runs at `http://localhost:5173`.

The storefront displays active catalog products and variant prices from the
public API, with password recovery at `/forgot-password`, cart at `/cart`, and
guest checkout at `/checkout`. Customers with an authenticated session can also
check out; a guest order can be claimed when its owner later signs in. The order
page is `/orders/{uuid}`. The staff dashboard provides session login plus
catalog, inventory, a read-only order queue, review moderation, feedback, and
an operational analytics overview; sign in with a Django staff account. The
management screens require their matching model permissions. The order queue
shows item summaries but excludes customer contact/address details and prices.
Analytics is limited to operational counts and contains no financial totals or
customer message content. The initial management screens load at most 100
records.

### Local demo catalog

For local storefront, cart, and checkout testing, run this from the repository
root:

```powershell
python backend/manage.py seed_demo_catalog
```

This creates four clearly labeled demo products, six variants, and opening
stock. It is safe to rerun: existing demo rows and stock are not reset, and
non-demo catalog data is left alone. Do not use demo data in a shared or
production environment.

To remove the demo catalog after testing, run:

```powershell
python backend/manage.py clear_demo_catalog --confirm
```

Cleanup refuses to remove mixed-item or paid orders and products containing
non-demo variants.

## Available API endpoints

- `POST /api/v1/auth/register/` creates a customer account with a username,
  password and optional unique email address. Registration does not sign the
  customer in.
- `GET /api/v1/auth/csrf/` returns a CSRF token and sets the CSRF cookie.
- `POST /api/v1/auth/login/` starts a username/password session;
  `POST /api/v1/auth/logout/` ends it; `GET /api/v1/auth/me/` returns the
  authenticated user. Login and logout require the CSRF token.
- `POST /api/v1/auth/password-reset/` requests a reset email;
  `POST /api/v1/auth/password-reset/confirm/` validates the one-time token and
  sets the new password. Both endpoints require a CSRF token and are
  rate-limited. Requests return the same response whether or not the email is
  registered.
- `GET` and `POST /api/v1/auth/addresses/` list and create the authenticated
  customer's addresses. `GET`, `PATCH`, and `DELETE` on
  `/api/v1/auth/addresses/{id}/` manage an address owned by that customer.
- `GET /api/v1/catalog/categories/` lists active categories.
- `GET /api/v1/catalog/products/` lists active products with their active
  variants. Catalog and inventory lists support `page` and `page_size`
  (default 20, maximum 100).
- `GET /api/v1/catalog/variants/` lists sellable variants. Staff can create,
  update, and deactivate products and variants through the catalog endpoints.
  Each variant owns its SKU, price, pack quantity, and pack unit; create a
  product first, then add its variants.
- `GET /api/v1/inventory/balances/` returns on-hand package counts to staff
  with inventory permissions, including reserved and available quantities.
  `GET` and `POST
  /api/v1/inventory/movements/` provide the stock movement ledger. Movement
  entries are append-only and require a positive package quantity and reason.
- `GET` and `POST /api/v1/cart/` read the current cart and add a variant;
  `PATCH` and `DELETE /api/v1/cart/items/{id}/` update or remove a line.
  Guests are identified by an HttpOnly cart cookie; customer carts are tied to
  the signed-in account.
- `POST /api/v1/checkout/` creates a pending-payment order from the cart.
  `GET /api/v1/orders/` lists the signed-in customer's orders;
  `GET /api/v1/orders/{uuid}/` reads an owned order; and
  `POST /api/v1/orders/{uuid}/cancel/` cancels an unpaid order and releases its
  stock reservation.
- `GET /api/v1/orders/manage/` returns a paginated, read-only order queue to
  staff with `orders.view_order`. It includes order status, creation time, and
  item names/SKUs/quantities, but no customer contact/address details or prices.
- `GET /api/v1/reviews/products/{product_slug}/summary/` returns the public
  average rating and approved-review count. `GET` and `POST` on
  `/api/v1/reviews/products/{product_slug}/` list approved reviews and submit
  a 1-5-star review. Anyone can submit without purchase verification; reviews
  are pending until Customer Support approves them. Customer Support manages
  submissions at `/api/v1/reviews/manage/`. Review submissions are rate-limited.
- `POST /api/v1/feedback/` accepts private general, website, product, or service
  feedback from guests and customers. Customer Support can list and update
  submissions at `/api/v1/feedback/manage/`; these messages are never public.
- `GET /api/v1/analytics/overview/` is available to staff and returns aggregate
  catalog, inventory, order-status, review, and feedback counts plus the
  approved-review average. Order counts are status counts, not sales; financial
  totals and feedback contents are excluded.

Catalogue writes require the matching Django model permission and `is_staff`.
The `Store Manager` group receives category, product, variant, and inventory
permissions. The `Customer Support` group receives review-moderation and
feedback-management permissions. The `Order Manager` group receives
read-only order access. The `Marketing Manager` group remains available for
future modules. Run
`python backend/manage.py sync_staff_roles` after migrations, then assign
groups and `is_staff` only to authorized staff. Super Admin access uses
Django's `is_superuser` flag.

The catalog migration moves each existing product's SKU and price to a
default variant (`Default`, quantity `1 each`). Review default packaging for
existing products and edit it to match the actual sellable package. Stock
movement types are `receipt`, `return`, `sale`, `damage`,
`adjustment_increase`, and `adjustment_decrease`. Deleting a variant or
product with stock, cart, order, or review history is blocked; deactivate it
instead.

Checkout snapshots product names, SKUs, pack details, and prices onto an order.
It reserves the requested stock until payment is confirmed by a future payment
integration or the order is cancelled. No payment is processed yet, and there
is no automatic reservation expiry; pending orders can hold stock indefinitely.
Order totals currently contain only the items subtotal: currency formatting,
taxes, and delivery fees are not configured.

Browser clients must send requests with credentials enabled and include the
CSRF token in the `X-CSRFToken` header for login, logout, password reset, cart
changes, checkout, order cancellation, and submissions made by authenticated
users. Product details and reviews are at `/products/{slug}`; the private
feedback form is at `/feedback`.
The storefront reset-request form is at `/forgot-password`; emailed links open
`/reset-password`. In local development, reset emails are printed by Django's
console email backend in the backend terminal. The sender and frontend reset
URL are configurable with `DJANGO_DEFAULT_FROM_EMAIL` and
`PASSWORD_RESET_FRONTEND_URL`. Production defaults to Django's SMTP backend;
set `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`, `DJANGO_EMAIL_USE_TLS`,
`DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD`, and
`DJANGO_DEFAULT_FROM_EMAIL` for the chosen SMTP service. Do not use the console
backend in production. Configure
`CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` for the frontend origins.

## Quality checks

```powershell
python backend/manage.py check
python backend/manage.py test
npm run lint
npm run build
```

## Key decisions

- The backend is a modular Django monolith to keep deployment and transactional commerce rules simple.
- Next.js serves the public storefront for product discoverability; Vite powers the internal dashboard.
- PostgreSQL is the production target. SQLite keeps the initial local setup friction-free.
- No payment, mail, media-storage, analytics, or other paid-service credentials are included or connected.

See `docs/architecture.md` for module boundaries and
`docs/project-progress.md` for current implementation status and the
prioritized roadmap.
