# Architecture decisions

## Modular Django monolith

The backend is one Django deployment with bounded apps. It owns commerce rules,
permissions, validation, database writes, and APIs. We will add domain apps only
when their models and workflows begin, starting with `accounts`, `catalog`,
and `inventory`.

The modules are: `accounts`, `customers`, `catalog`, `inventory`, `cart`,
`orders`, `payments`, `delivery`, `promotions`, `loyalty`, `reviews`, `feedback`,
and `analytics`. Accounts, catalog, inventory, cart, orders, reviews, and
feedback are present, as is a staff-only operational analytics overview.
Payment, delivery, promotions, and loyalty remain deferred. Platinum scope
excludes wholesale automation for this release.

## Frontend boundaries

- `frontend/storefront`: Next.js public commerce site, optimised for discoverable product pages.
- `frontend/admin`: React/Vite internal operations dashboard, not public or SEO-focused.
- Both clients consume `/api/v1/`; neither owns business rules or writes to the database directly.

## Local development

SQLite is the zero-configuration default. PostgreSQL is the intended shared and
production database, enabled by environment variables once a local database is
available. Redis, Celery, payment providers, and object storage are
deliberately deferred until their operational choices are approved. Password
reset uses Django's email backend: local development prints messages to the
backend console, while production email delivery must be configured with the
chosen SMTP service.

## Account and catalogue foundation

The account, catalogue, inventory, cart, and order foundations are implemented: a
customer profile associated with Django's built-in user, customer registration,
categories, products, sellable variants, stock balances, an append-only stock
movement ledger, guest/customer carts, order snapshots, pending-payment stock
reservations, moderated product reviews, and private feedback submissions.
Catalogue and approved-review reads are public; inventory and feedback
management require staff permissions.

Confirmed account decisions:

- Customers sign in with a username.
- Existing local user records must be preserved; do not replace the user model.
- Customer email is optional, but unique when provided.
- Retail and business customers use the same prices at launch.

Registration creates an account but does not sign the customer in. Session
login, logout, current-user lookup, and CSRF protection are implemented.
Password reset uses Django's expiring, single-use tokens and password
validators. Requests do not disclose whether an email is registered, and the
reset endpoints require CSRF protection and are rate-limited; the storefront
provides request and confirmation screens.
Customer address list/create/detail/update/delete endpoints are implemented
and scoped to the authenticated customer. The `sync_staff_roles` command
creates initial groups; `Store Manager` receives category, product, variant,
and inventory permissions; `Order Manager` receives read-only order access.
The order queue omits contact details, addresses, and prices. `Super Admin` is
represented by Django's `is_superuser` flag. Address default-selection
behavior is not implemented.
Guests are identified by a random HttpOnly cart cookie protected by CSRF; their
orders are claimable by the same customer after login. Checkout reserves stock
until payment confirmation or cancellation. A payment provider, automatic
reservation expiry, tax, shipping fees, and currency have not been defined, so
orders remain pending and their amounts currently represent the item subtotal
only. The remaining staff and customer workflows should use the established
API contracts rather than duplicating business rules.

Product reviews accept guest or customer submissions with a 1-5 rating.
Reviews remain pending until Customer Support approves them; only approved
reviews contribute to public product ratings. General customer feedback is
private to authorized staff. Customer Support permissions are assigned by
`sync_staff_roles`; the admin dashboard displays only sections allowed by the
signed-in staff member's permissions.

The staff-only analytics overview aggregates active catalog items, package
stock, order statuses, review statuses/ratings, and feedback statuses. It
excludes monetary totals and feedback contents; order status counts are not
sales reporting.

The product-to-variant migration preserves existing product SKUs and prices
as default variants. Pack quantities and units are flexible labels; bulk
catalog import requirements remain future work. Cart lines do not reserve
stock. Transactional order placement revalidates availability, creates
immutable item snapshots, and reserves stock. A later payment integration must
call the internal order-payment service only after verified provider
confirmation; browser redirects must not mark an order paid.
