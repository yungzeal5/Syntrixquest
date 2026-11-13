# Syntrix Quest Project Progress

**Last reviewed:** 2026-11-13
**Status:** Foundation, catalog/inventory, cart/orders, reviews/feedback, staff
operational analytics, and the read-only staff order queue are implemented.
Local-only mock catalog data is available for testing. Payment, tax, shipping,
and fulfillment remain unconfigured.

## A. Existing project assessment

- The repository is an npm-workspace monorepo with a Django REST API, a Next.js
  storefront, and a React/Vite admin application.
- Django has `core`, `accounts`, `catalog`, `inventory`, `cart`, `orders`,
  `reviews`, `feedback`, and `analytics` apps. Its data
  model includes Django's default user, a one-to-one customer profile,
  categories, products, sellable variants, stock balances, and stock movements.
- Customer registration is implemented at `/api/v1/auth/register/`. Customers
  sign in with usernames; email is optional and unique when provided. The
  registration flow does not sign the customer in.
- Session login/logout and current-user lookup are implemented. The CSRF
  endpoint sets a token cookie, and unsafe session endpoints require the
  matching token.
- Password reset is implemented end to end. Reset requests do not reveal
  whether an email is registered; confirmation uses Django's expiring,
  single-use token and password validators. Both endpoints require CSRF and
  are rate-limited. Local emails use Django's console backend; production SMTP
  configuration remains an operational deployment task.
- Customers can list, create, retrieve, update, and delete their own addresses.
  Address rows are scoped by the authenticated user; the API does not expose a
  default-address field or allow a customer to assign ownership.
- Staff role groups are bootstrapped by `python manage.py sync_staff_roles`.
  Catalogue writes require `is_staff` and the matching model permission.
  `Store Manager` can manage categories/products/variants and view balances or
  record inventory movements. `Order Manager` has read-only access to the
  staff order queue.
- The API exposes paginated category, product, and variant endpoints.
  Product SKUs and prices live on variants; existing product rows migrate to a
  default variant. Inventory movement entries update on-hand balances in a
  transaction and cannot be edited or deleted through the API. Pending orders
  reserve stock; inventory adjustments cannot consume reserved quantities.
- Guest and authenticated carts, checkout, order snapshots, owner-scoped order
  retrieval, and cancellation are implemented. Guest carts use a hashed
  HttpOnly cookie token; a guest order can be claimed after sign-in with that
  same token. Orders remain pending payment until a future payment integration
  confirms a charge.
- SQLite is the local default. Settings can be configured for PostgreSQL, and a
  PostgreSQL driver is present.
- The storefront now renders active products and their sellable variants from
  the catalog API, and provides password-reset, cart, checkout, guest order,
  product details/reviews, and private feedback pages. The admin provides
  staff session login, catalog/inventory screens, review moderation, a private
  feedback inbox, a read-only order queue, and an operational analytics
  overview. The order queue excludes customer contact/address details and
  prices. Admin lists load at most 100 records.
- Guests and customers may submit 1-5-star product reviews; all reviews remain
  pending until approved by Customer Support. Only approved reviews affect
  public product rating summaries. Feedback is private and can be submitted
  without an account; Customer Support can update its status and internal notes.
- `seed_demo_catalog` creates clearly labeled local demo products, variants,
  and opening stock without resetting existing demo stock or touching
  non-demo catalog rows. `clear_demo_catalog --confirm` is available for
  explicit cleanup and refuses paid/mixed orders or non-demo variants.
- `docs/architecture.md` documents the modular-monolith direction. The
  supplied sequence puts database/authentication before commerce workflows;
  that order is preserved.
- No payment provider, Redis/Celery, object storage, production deployment, or
  operational backup configuration is in place.

## B. Proposed repository architecture

- Keep one Django REST API as the authority for identity, catalogue, prices,
  stock, orders, payments, delivery, and permissions.
- Keep the Next.js storefront for customer discovery and shopping, and the
  Vite application for staff operations. Neither frontend should calculate
  authoritative prices or write directly to the database.
- Keep the current Django apps and add domain apps only as their workflows are
  implemented: `customers`, `inventory`, `cart`, `orders`, `payments`,
  `delivery`, `promotions`, `loyalty`, `reviews`, `feedback`, and `analytics`.
- Put business operations that span multiple models in service functions,
  protected by database transactions. Keep HTTP handling in views/viewsets,
  validation in serializers, and access rules in permission classes.
- Use PostgreSQL for shared and production environments; retain SQLite for
  lightweight local development only.

## C. Proposed database schema

Implement incrementally, not as one large migration:

1. **Identity:** retain Django's existing user/account model; customer profile;
   customer addresses; Django groups and permissions for staff roles.
2. **Catalogue:** category tree; product; sellable product variant/SKU; product
   media; explicit packaging and quantity attributes. Put price and stock at the
   sellable variant level.
3. **Inventory:** one balance per variant and an append-only stock-movement
   ledger recording adjustments, receipts, reservations, releases, and sales.
4. **Commerce:** carts and cart items, orders and immutable order items, and
   active stock reservations are implemented. Payment-status history and
   automatic order expiry remain pending.
5. **Money and fulfilment:** payment attempts/transactions and idempotent
   provider events; delivery zones and fee rules; delivery assignments and
   status history.
6. **Growth modules:** promotions/coupons, loyalty account and transaction
   ledger, product reviews, general feedback, and report queries/exports.

## D. Model relationship principles

- A category may have a parent category. A product belongs to a category and
  has one or more variants; each variant is independently purchasable and owns
  its SKU, pack size, price, and inventory.
- A customer account can have multiple addresses. Carts belong to a customer
  when authenticated or use a hashed guest token; guest orders can be claimed
  after sign-in with that token.
- An order belongs to a customer when available and contains immutable order
  lines. Payment state and fulfilment state are separate; both have histories.
- Inventory movements and loyalty transactions are ledgers, not mutable
  balance-only records. Active order reservations reduce available stock and
  are released on cancellation or converted to a sale after payment
  confirmation.
- Reviews reference a product and optionally a customer account; feedback
  remains a separate, private entity.
- Add database constraints for unique SKUs, non-negative amounts/quantities,
  and valid state transitions where feasible. Use transactions and row locking
  for checkout and stock changes.

## E. Authentication and permissions proposal

- Use the confirmed username sign-in with Django's existing user model.
  Customer email is optional and unique when provided; preserve staff access
  through Django's existing permissions.
- Use Django session authentication for first-party web clients. The browser
  obtains a CSRF token from `/api/v1/auth/csrf/`, sends credentials, and
  includes `X-CSRFToken` on unsafe session and password-reset requests.
- Use Django groups/permissions for staff roles rather than a hard-coded role
  string. Enforce object-level access for customer-owned profiles, addresses,
  carts, and orders.
- For first-party web clients, prefer session authentication with CSRF
  protection when deployed under the same site. Configure explicit CORS and
  trusted origins for local development. Do not rely on Basic Authentication
  for production browser sessions.
- Keep public catalogue reads separate from authenticated customer actions and
  staff-only operations. Catalogue writes now require model permissions and
  `is_staff`. Add throttling to authentication and other abuse-prone endpoints
  before public launch.

## F. Proposed API structure

Continue the `/api/v1/` prefix and add versioned domain endpoints as workflows
are implemented:

- `/health/`
- `/auth/` including registration, session lifecycle, and customer addresses
- `/customers/` for future customer profile operations
- `/catalog/categories/`, `/catalog/products/`, `/catalog/variants/`
- `/inventory/`
- `/cart/`, `/checkout/`, and `/orders/` are implemented; `/payments/` remains
  planned.
- `/reviews/` provides public approved reviews and rating summaries plus
  Customer Support moderation; `/feedback/` accepts private customer feedback
  and provides a Customer Support inbox.
- `/delivery/`, `/promotions/`, `/loyalty/`
- `/reviews/`, `/feedback/`, and `/reports/`

Use pagination, filtering, stable error shapes, and explicit permissions.
Calculate prices, discounts, delivery fees, and stock availability on the
server. Do not mark an order paid based on a browser redirect.

## G. Technical risks and open decisions

- **Account model:** `CustomerProfile` points to Django's default user.
  Username sign-in and preservation of local accounts are confirmed. The new
  optional customer email has a database uniqueness constraint.
- **Variants and pricing:** SKU and price now live on sellable variants, and
  existing products migrate to a default `1 each` variant. Review the package
  quantity/unit for any existing catalog data. Business and retail customers
  use the same prices at launch; later price differentiation needs an approved
  decision.
- **Security configuration:** settings default to `DEBUG=True` and a known
  development secret. Production must fail closed without a real secret,
  explicit hosts, secure cookies/HTTPS settings, and production CORS/CSRF
  configuration.
- **Permissions and tests:** registration, session login/logout, password
  reset, customer-owned address CRUD, and initial staff group permissions
  exist. The local database had no non-superuser staff accounts when the
  catalogue permission policy changed.
- **Role scope:** `Store Manager` can manage catalog categories, products, and
  variants, and can view balances and record stock movements. Other role
  groups remain without model permissions until their business modules exist.
  Super Admin uses Django's superuser flag. Assign `is_staff` and groups to
  staff accounts through Django Admin.
- **Address behavior:** no default-address policy is defined or implemented.
- **Commerce policy:** guest and registered checkout are supported. Pending
  orders reserve stock until payment confirmation or cancellation, with no
  automatic expiry. The payment provider is not selected; item subtotal is the
  only calculated amount because currency, tax, and delivery fee rules remain
  undefined.
- **Reviews and feedback:** any visitor may submit a product rating/review.
  Customer Support approval is required before publication. Feedback may be
  submitted by guests and customers and is visible only to authorized staff.
- **Operations:** PostgreSQL, backups, media storage, production email
  credentials, payment provider, and deployment settings remain unconfigured.
- **Dependency state:** local npm installs had incomplete packages and native
  bindings. Local workspace installs were repaired without editing manifests.
  npm reported seven moderate advisories during storefront dependency repair;
  they have not been individually triaged.
- **Roadmap sequencing:** the core Milestone 2 authentication contracts and the
  initial commerce API/UI contracts are in place. Payment and fulfilment
  policies must be decided before accepting real orders.

## H. Prioritized implementation plan

1. **Milestone 1 — foundation and architecture.** Repository structure, local
   run commands, baseline apps, and initial architecture notes exist. Record
   decisions and keep operational setup reproducible.
2. **Milestone 2 — database schema and authentication.** Customer
   registration, session login/logout, password reset, address ownership, and
   initial staff role permissions are implemented. Configure production email
   delivery before launch.
3. **Milestone 3 — catalogue and inventory.** Variant-level SKUs, prices,
   flexible pack quantities, staff catalog APIs, pagination, stock balances,
   and audited inventory movements are implemented. Initial storefront and
   admin screens are connected to these APIs. Define bulk import requirements
   and checkout-driven reservations before extending inventory workflows.
   Business and retail customers use the same prices at launch.
4. **Milestone 4 — cart and orders.** Guest/customer carts, pending-payment
   checkout, immutable order-line snapshots, and stock reservations/releases
   are implemented. Select a payment provider and define currency, tax, and
   delivery rules before processing payments.
5. **Milestone 5 — reviews and feedback.** Product ratings, moderated reviews,
   private feedback submissions, Customer Support permissions, and the staff
   inbox are implemented.
6. **Milestone 6 — operational analytics.** Staff can view aggregate catalog,
   inventory, order-status, review, and feedback metrics. Financial totals and
   feedback contents are excluded.
7. **Milestone 7 — staff order visibility.** The Order Manager group can view
   a paginated order queue with status and item summaries only. It has no
   customer contact/address details, price totals, or mutation actions.
8. Payment, delivery, promotions, loyalty, broader security/performance work,
   deployment, and handover are explicitly deferred for a later phase.

## Verification snapshot

- Django system check: passed.
- Django tests: 56 passed in the full-suite run, including the staff order
  queue, analytics, reviews, feedback, permissions, and demo seed/cleanup
  safety.
- Migration consistency check: passed; cart, order, review, and feedback
  migrations are applied locally.
- Storefront lint and production build: passed with product details, ratings,
  reviews, private feedback, cart, checkout, and order pages.
- Account migrations: applied; existing user records are preserved.
- Staff role groups: bootstrapped; Store Manager has catalog/inventory
  permissions, Customer Support has review/feedback permissions, and Order
  Manager has read-only order access.
- Admin production build: passed.
- Storefront ESLint and admin Oxlint: passed after local dependency repair;
  Oxlint reports two non-fatal effect/state warnings in existing catalog and
  inventory refresh flows.
- Storefront catalog, password-reset, cart, checkout, order, product reviews,
  and feedback UI plus admin catalog, inventory, moderation, feedback inbox,
  read-only order queue, and analytics build successfully. Payment, automatic
  reservation expiry, delivery fees, tax, currency formatting, promotions,
  loyalty, and bulk import remain deferred; admin lists are limited to the
  first 100 records.
- Demo catalog seed/cleanup commands and their safety tests are included;
  run `python backend/manage.py seed_demo_catalog` for local test data.

## Decisions still pending

- Select the payment provider and confirm supported payment methods before
  enabling payment processing.
- Confirm business pricing beyond launch, if it will differ from retail prices.
- Agree delivery zones and fee rules before implementing delivery workflows.
- Define bulk catalog import fields and validation before implementing import.
