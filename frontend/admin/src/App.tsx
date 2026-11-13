import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  ApiError,
  createCategory,
  createProduct,
  createVariant,
  fetchOperationsOverview,
  fetchBalances,
  fetchCategories,
  fetchManagedFeedback,
  fetchManagedOrders,
  fetchManagedReviews,
  fetchMovements,
  fetchProducts,
  fetchVariants,
  getCurrentUser,
  login,
  logout,
  recordMovement,
  setProductActive,
  setProductReviewStatus,
  setVariantActive,
  updateManagedFeedback,
} from "./api";
import type {
  Category,
  FeedbackStatus,
  ManagedFeedback,
  ManagedOrder,
  ManagedProductReview,
  OperationsOverview,
  Product,
  ProductVariant,
  ProductReviewStatus,
  SessionUser,
  StockBalance,
  StockMovement,
} from "./api";
import "./App.css";

type DashboardTab =
  | "catalog"
  | "inventory"
  | "orders"
  | "reviews"
  | "feedback"
  | "analytics";
type Message = { text: string; error: boolean } | null;

const MOVEMENT_TYPES = [
  ["receipt", "Receipt"],
  ["return", "Customer return"],
  ["sale", "Sale"],
  ["damage", "Damaged stock"],
  ["adjustment_increase", "Adjustment increase"],
  ["adjustment_decrease", "Adjustment decrease"],
] as const;

function messageFromError(error: unknown) {
  return error instanceof Error
    ? error.message
    : "The request could not be completed.";
}

function formatPrice(price: string) {
  return Number(price).toFixed(2);
}

function LoginPanel({ onLogin }: { onLogin: (user: SessionUser) => void }) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setPending(true);
    const formData = new FormData(event.currentTarget);
    const username = formData.get("username");
    const password = formData.get("password");

    if (typeof username !== "string" || typeof password !== "string") {
      setError("Enter your username and password.");
      setPending(false);
      return;
    }

    try {
      onLogin(await login(username, password));
    } catch (loginError) {
      setError(messageFromError(loginError));
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <p className="eyebrow">Syntrix Quest</p>
        <h1>Staff sign in</h1>
        <p className="muted">
          Sign in with your Django staff account to open the tools assigned to your role.
        </p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            Username
            <input autoComplete="username" name="username" required />
          </label>
          <label>
            Password
            <input
              autoComplete="current-password"
              name="password"
              required
              type="password"
            />
          </label>
          <button className="button button-primary" disabled={pending}>
            {pending ? "Signing in..." : "Sign in"}
          </button>
        </form>
        {error && <p className="notice notice-error">{error}</p>}
      </section>
    </main>
  );
}

function CatalogPanel() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState<Message>(null);

  const refresh = useCallback(async () => {
    try {
      const [nextCategories, nextProducts] = await Promise.all([
        fetchCategories(),
        fetchProducts(),
      ]);
      setCategories(nextCategories);
      setProducts(nextProducts);
    } catch (loadError) {
      setError(messageFromError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function handleRefresh() {
    setError("");
    setLoading(true);
    void refresh();
  }

  async function handleCategorySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = formData.get("name");
    const slug = formData.get("slug");
    if (typeof name !== "string" || typeof slug !== "string") {
      setNotice({ text: "Enter a category name and slug.", error: true });
      return;
    }

    setPending(true);
    setNotice(null);
    try {
      await createCategory({ name, slug });
      form.reset();
      setNotice({ text: "Category created.", error: false });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    } finally {
      setPending(false);
    }
  }

  async function handleProductSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = formData.get("name");
    const slug = formData.get("slug");
    const description = formData.get("description");
    const categoryId = Number(formData.get("category_id"));
    if (
      typeof name !== "string" ||
      typeof slug !== "string" ||
      typeof description !== "string" ||
      !Number.isInteger(categoryId) ||
      categoryId < 1
    ) {
      setNotice({ text: "Complete all product fields.", error: true });
      return;
    }

    setPending(true);
    setNotice(null);
    try {
      await createProduct({ name, slug, description, category_id: categoryId });
      form.reset();
      setNotice({
        text: "Product created. Add at least one active variant to publish it.",
        error: false,
      });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    } finally {
      setPending(false);
    }
  }

  async function handleVariantSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const productId = Number(formData.get("product_id"));
    const label = formData.get("label");
    const sku = formData.get("sku");
    const packQuantity = formData.get("pack_quantity");
    const packUnit = formData.get("pack_unit");
    const price = formData.get("price");
    if (
      !Number.isInteger(productId) ||
      productId < 1 ||
      typeof label !== "string" ||
      typeof sku !== "string" ||
      typeof packQuantity !== "string" ||
      typeof packUnit !== "string" ||
      typeof price !== "string"
    ) {
      setNotice({ text: "Complete all variant fields.", error: true });
      return;
    }

    setPending(true);
    setNotice(null);
    try {
      await createVariant({
        product_id: productId,
        label,
        sku,
        pack_quantity: packQuantity,
        pack_unit: packUnit,
        price,
      });
      form.reset();
      setNotice({ text: "Product variant created.", error: false });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    } finally {
      setPending(false);
    }
  }

  async function toggleProduct(product: Product) {
    setNotice(null);
    try {
      await setProductActive(product.slug, !product.is_active);
      setNotice({
        text: `Product ${product.is_active ? "deactivated" : "activated"}.`,
        error: false,
      });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    }
  }

  async function toggleVariant(variant: ProductVariant) {
    setNotice(null);
    try {
      await setVariantActive(variant.id, !variant.is_active);
      setNotice({
        text: `Variant ${variant.is_active ? "deactivated" : "activated"}.`,
        error: false,
      });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    }
  }

  return (
    <section className="panel-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Store setup</p>
          <h2>Catalog</h2>
        </div>
        <button className="button button-secondary" onClick={handleRefresh}>
          Refresh
        </button>
      </div>

      {error && <p className="notice notice-error">{error}</p>}
      {notice && (
        <p className={`notice ${notice.error ? "notice-error" : "notice-ok"}`}>
          {notice.text}
        </p>
      )}

      <div className="form-grid">
        <form className="card form-stack" onSubmit={handleCategorySubmit}>
          <h3>Add category</h3>
          <label>
            Name
            <input maxLength={120} name="name" required />
          </label>
          <label>
            URL slug
            <input maxLength={50} name="slug" required />
          </label>
          <button className="button button-primary" disabled={pending}>
            Create category
          </button>
        </form>

        <form className="card form-stack" onSubmit={handleProductSubmit}>
          <h3>Add product</h3>
          <label>
            Name
            <input maxLength={200} name="name" required />
          </label>
          <label>
            URL slug
            <input maxLength={50} name="slug" required />
          </label>
          <label>
            Category
            <select
              defaultValue=""
              disabled={categories.length === 0}
              name="category_id"
              required
            >
              <option disabled value="">
                {categories.length === 0
                  ? "Create a category first"
                  : "Select a category"}
              </option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Description
            <textarea maxLength={5000} name="description" rows={3} />
          </label>
          <button
            className="button button-primary"
            disabled={pending || categories.length === 0}
          >
            Create product
          </button>
        </form>

        <form className="card form-stack" onSubmit={handleVariantSubmit}>
          <h3>Add sellable variant</h3>
          <label>
            Product
            <select defaultValue="" name="product_id" required>
              <option disabled value="">
                Select a product
              </option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Pack label
            <input maxLength={100} name="label" placeholder="Pack of 50" required />
          </label>
          <div className="field-row">
            <label>
              Pack quantity
              <input
                min="0.001"
                name="pack_quantity"
                required
                step="0.001"
                type="number"
              />
            </label>
            <label>
              Pack unit
              <input
                defaultValue="each"
                maxLength={32}
                name="pack_unit"
                required
              />
            </label>
          </div>
          <div className="field-row">
            <label>
              SKU
              <input maxLength={64} name="sku" required />
            </label>
            <label>
              Price
              <input min="0" name="price" required step="0.01" type="number" />
            </label>
          </div>
          <button
            className="button button-primary"
            disabled={pending || products.length === 0}
          >
            Create variant
          </button>
        </form>
      </div>

      <div className="card">
        <div className="section-heading">
          <h3>Products</h3>
          <span className="muted">{products.length} loaded</span>
        </div>
        {loading ? (
          <p className="muted">Loading catalog...</p>
        ) : products.length === 0 ? (
          <p className="muted">No products found. Create a product to begin.</p>
        ) : (
          <div className="product-list">
            {products.map((product) => (
              <article className="product-row" key={product.id}>
                <div className="product-topline">
                  <div>
                    <p className="eyebrow">{product.category.name}</p>
                    <h4>{product.name}</h4>
                    <p className="muted">
                      {product.slug} · {product.variants.length} variant
                      {product.variants.length === 1 ? "" : "s"}
                    </p>
                  </div>
                  <button
                    className="button button-secondary"
                    onClick={() => void toggleProduct(product)}
                  >
                    {product.is_active ? "Deactivate" : "Activate"}
                  </button>
                </div>
                {product.variants.length > 0 && (
                  <div className="variant-list">
                    {product.variants.map((variant) => (
                      <div className="variant-row" key={variant.id}>
                        <div>
                          <strong>{variant.label}</strong>
                          <span className="muted">
                            {variant.sku} · {variant.pack_quantity}{" "}
                            {variant.pack_unit} · {formatPrice(variant.price)}
                            {variant.is_default ? " · Default" : ""}
                          </span>
                        </div>
                        <button
                          className="text-button"
                          onClick={() => void toggleVariant(variant)}
                        >
                          {variant.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function InventoryPanel() {
  const [variants, setVariants] = useState<ProductVariant[]>([]);
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState<Message>(null);

  const refresh = useCallback(async () => {
    try {
      const [nextVariants, nextBalances, nextMovements] = await Promise.all([
        fetchVariants(),
        fetchBalances(),
        fetchMovements(),
      ]);
      setVariants(nextVariants);
      setBalances(nextBalances);
      setMovements(nextMovements);
    } catch (loadError) {
      setError(messageFromError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function handleRefresh() {
    setError("");
    setLoading(true);
    void refresh();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const variantId = Number(formData.get("variant_id"));
    const movementType = formData.get("movement_type");
    const quantity = Number(formData.get("quantity"));
    const reason = formData.get("reason");
    if (
      !Number.isInteger(variantId) ||
      variantId < 1 ||
      typeof movementType !== "string" ||
      !Number.isInteger(quantity) ||
      quantity < 1 ||
      typeof reason !== "string"
    ) {
      setNotice({ text: "Enter a valid variant, quantity, and reason.", error: true });
      return;
    }

    setPending(true);
    setNotice(null);
    try {
      await recordMovement({
        variant_id: variantId,
        movement_type: movementType,
        quantity,
        reason,
      });
      form.reset();
      setNotice({ text: "Stock movement recorded.", error: false });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    } finally {
      setPending(false);
    }
  }

  const activeVariants = variants.filter((variant) => variant.is_active);

  return (
    <section className="panel-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">On-hand stock</p>
          <h2>Inventory</h2>
        </div>
        <button className="button button-secondary" onClick={handleRefresh}>
          Refresh
        </button>
      </div>

      {error && <p className="notice notice-error">{error}</p>}
      {notice && (
        <p className={`notice ${notice.error ? "notice-error" : "notice-ok"}`}>
          {notice.text}
        </p>
      )}

      <div className="card">
        <h3>Record stock movement</h3>
        <p className="muted">
          Quantities are counted in sellable packs. Each entry is permanent in
          the stock ledger.
        </p>
        <form className="movement-form" onSubmit={handleSubmit}>
          <label>
            Variant
            <select
              defaultValue=""
              disabled={activeVariants.length === 0}
              name="variant_id"
              required
            >
              <option disabled value="">
                {activeVariants.length === 0
                  ? "Add an active variant first"
                  : "Select a variant"}
              </option>
              {activeVariants.map((variant) => (
                <option key={variant.id} value={variant.id}>
                  {variant.product} · {variant.label} ({variant.sku})
                </option>
              ))}
            </select>
          </label>
          <label>
            Movement
            <select defaultValue="receipt" name="movement_type">
              {MOVEMENT_TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Packages
            <input min="1" name="quantity" required step="1" type="number" />
          </label>
          <label>
            Reason
            <input maxLength={500} name="reason" required />
          </label>
          <button
            className="button button-primary"
            disabled={pending || activeVariants.length === 0}
          >
            {pending ? "Recording..." : "Record movement"}
          </button>
        </form>
      </div>

      <div className="inventory-grid">
        <div className="card">
          <div className="section-heading">
            <h3>Stock balances</h3>
            <span className="muted">{balances.length} variants</span>
          </div>
          {loading ? (
            <p className="muted">Loading stock...</p>
          ) : balances.length === 0 ? (
            <p className="muted">No stock balances found.</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Product / variant</th>
                    <th>SKU</th>
                    <th>On hand</th>
                  </tr>
                </thead>
                <tbody>
                  {balances.map((balance) => (
                    <tr key={balance.variant_id}>
                      <td>
                        {balance.product_name}
                        <span className="table-subtitle">
                          {balance.variant_label}
                        </span>
                      </td>
                      <td>{balance.sku}</td>
                      <td>{balance.quantity_on_hand}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card">
          <div className="section-heading">
            <h3>Recent movements</h3>
            <span className="muted">{movements.length} loaded</span>
          </div>
          {loading ? (
            <p className="muted">Loading movements...</p>
          ) : movements.length === 0 ? (
            <p className="muted">No stock movements recorded yet.</p>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Movement</th>
                    <th>SKU</th>
                    <th>Qty</th>
                    <th>Reason / staff</th>
                  </tr>
                </thead>
                <tbody>
                  {movements.map((movement) => (
                    <tr key={movement.id}>
                      <td>{movement.movement_type.replaceAll("_", " ")}</td>
                      <td>{movement.variant_sku}</td>
                      <td>{movement.quantity}</td>
                      <td>
                        {movement.reason}
                        <span className="table-subtitle">
                          {movement.created_by ?? "System"} ·{" "}
                          {new Date(movement.created_at).toLocaleString()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function AnalyticsCard({
  title,
  metrics,
}: {
  title: string;
  metrics: { label: string; value: string | number }[];
}) {
  return (
    <section className="card analytics-card">
      <h3>{title}</h3>
      <dl className="analytics-metrics">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <dt>{metric.label}</dt>
            <dd>{metric.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function OrderQueuePanel() {
  const [orders, setOrders] = useState<ManagedOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setOrders(await fetchManagedOrders());
      setError("");
    } catch (loadError) {
      setError(messageFromError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchManagedOrders()
      .then((nextOrders) => {
        if (active) {
          setOrders(nextOrders);
          setError("");
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(messageFromError(loadError));
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
  }, []);

  function handleRefresh() {
    setLoading(true);
    void refresh();
  }

  return (
    <section className="panel-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Read-only operations</p>
          <h2>Order queue</h2>
        </div>
        <button
          className="button button-secondary"
          disabled={loading}
          onClick={handleRefresh}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>
      <p className="muted">
        Shows the 100 newest orders and item summaries only. Customer contact
        details, addresses, and prices are not included.
      </p>
      {error && <p className="notice notice-error">{error}</p>}
      <div className="card">
        {loading ? (
          <p className="muted">Loading orders...</p>
        ) : orders.length === 0 ? (
          <p className="muted">No orders have been placed.</p>
        ) : (
          <div className="product-list">
            {orders.map((order) => (
              <article className="product-row" key={order.public_id}>
                <div className="product-topline">
                  <div>
                    <p className="eyebrow">Order reference</p>
                    <h3>{order.public_id}</h3>
                    <p className="muted">
                      Placed {new Date(order.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="status-pill">
                    {order.status.replaceAll("_", " ")}
                  </span>
                </div>
                <ul className="order-item-list">
                  {order.items.map((item) => (
                    <li key={item.sku}>
                      <span>
                        {item.quantity} x {item.product_name} ({item.variant_label})
                      </span>
                      <span className="muted">{item.sku}</span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function AnalyticsPanel() {
  const [overview, setOverview] = useState<OperationsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setOverview(await fetchOperationsOverview());
      setError("");
    } catch (loadError) {
      setError(messageFromError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  function handleRefresh() {
    setLoading(true);
    void refresh();
  }

  useEffect(() => {
    let active = true;
    fetchOperationsOverview()
      .then((nextOverview) => {
        if (active) {
          setOverview(nextOverview);
          setError("");
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(messageFromError(loadError));
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
  }, []);

  return (
    <section className="panel-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Operational overview</p>
          <h2>Analytics</h2>
        </div>
        <button
          className="button button-secondary"
          disabled={loading}
          onClick={handleRefresh}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <p className="notice notice-error">{error}</p>}
      {loading && !overview ? (
        <p className="muted">Loading operational metrics...</p>
      ) : overview ? (
        <>
          <div className="analytics-grid">
            <AnalyticsCard
              title="Catalog"
              metrics={[
                { label: "Active products", value: overview.catalog.active_products },
                { label: "Active variants", value: overview.catalog.active_variants },
              ]}
            />
            <AnalyticsCard
              title="Inventory"
              metrics={[
                { label: "Packages on hand", value: overview.inventory.packages_on_hand },
                { label: "Packages reserved", value: overview.inventory.packages_reserved },
                { label: "Packages available", value: overview.inventory.packages_available },
              ]}
            />
            <AnalyticsCard
              title="Orders by status"
              metrics={[
                { label: "Pending payment", value: overview.orders.pending_payment },
                { label: "Paid", value: overview.orders.paid },
                { label: "Cancelled", value: overview.orders.cancelled },
              ]}
            />
            <AnalyticsCard
              title="Reviews"
              metrics={[
                { label: "Pending", value: overview.reviews.pending },
                { label: "Approved", value: overview.reviews.approved },
                { label: "Rejected", value: overview.reviews.rejected },
                {
                  label: "Average approved rating",
                  value: overview.reviews.average_approved_rating,
                },
              ]}
            />
            <AnalyticsCard
              title="Feedback by status"
              metrics={[
                { label: "New", value: overview.feedback.new },
                { label: "In progress", value: overview.feedback.in_progress },
                { label: "Resolved", value: overview.feedback.resolved },
              ]}
            />
          </div>
          <p className="muted">
            Order figures are status counts only, not sales or revenue. This
            overview contains no financial totals or customer message content.
          </p>
        </>
      ) : null}
    </section>
  );
}

function ReviewsPanel() {
  const [reviews, setReviews] = useState<ManagedProductReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState<Message>(null);

  const refresh = useCallback(async () => {
    try {
      setReviews(await fetchManagedReviews());
      setError("");
    } catch (loadError) {
      setError(messageFromError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchManagedReviews()
      .then((nextReviews) => {
        if (active) {
          setReviews(nextReviews);
          setError("");
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(messageFromError(loadError));
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
  }, []);

  async function changeStatus(
    review: ManagedProductReview,
    status: ProductReviewStatus,
  ) {
    setPendingId(review.id);
    setNotice(null);
    try {
      await setProductReviewStatus(review.id, status);
      setNotice({
        text: `Review ${status}.`,
        error: false,
      });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    } finally {
      setPendingId(null);
    }
  }

  return (
    <section className="panel-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Customer content</p>
          <h2>Product reviews</h2>
        </div>
        <button
          className="button button-secondary"
          onClick={() => {
            setLoading(true);
            void refresh();
          }}
        >
          Refresh
        </button>
      </div>
      <p className="muted">
        Only approved reviews appear on the storefront. Up to 100 reviews are
        loaded at a time.
      </p>
      {error && <p className="notice notice-error">{error}</p>}
      {notice && (
        <p className={`notice ${notice.error ? "notice-error" : "notice-ok"}`}>
          {notice.text}
        </p>
      )}
      <div className="card">
        {loading ? (
          <p className="muted">Loading reviews...</p>
        ) : reviews.length === 0 ? (
          <p className="muted">No reviews have been submitted.</p>
        ) : (
          <div className="product-list">
            {reviews.map((review) => (
              <article className="product-row" key={review.id}>
                <div className="product-topline">
                  <div>
                    <p className="eyebrow">{review.product_name}</p>
                    <h3>{review.title || `${review.rating} out of 5 stars`}</h3>
                    <p className="muted">
                      {review.display_name} · {review.rating}/5 ·{" "}
                      {new Date(review.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="status-pill">{review.status}</span>
                </div>
                <p className="review-body">{review.body}</p>
                <div className="action-row">
                  {review.status !== "approved" && (
                    <button
                      className="button button-primary"
                      disabled={pendingId === review.id}
                      onClick={() => void changeStatus(review, "approved")}
                    >
                      Approve
                    </button>
                  )}
                  {review.status !== "rejected" && (
                    <button
                      className="button button-secondary"
                      disabled={pendingId === review.id}
                      onClick={() => void changeStatus(review, "rejected")}
                    >
                      Reject
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function FeedbackPanel() {
  const [feedback, setFeedback] = useState<ManagedFeedback[]>([]);
  const [drafts, setDrafts] = useState<
    Record<number, { status: FeedbackStatus; staff_notes: string }>
  >({});
  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState<Message>(null);

  const refresh = useCallback(async () => {
    try {
      const nextFeedback = await fetchManagedFeedback();
      const nextDrafts: Record<
        number,
        { status: FeedbackStatus; staff_notes: string }
      > = {};
      nextFeedback.forEach((item) => {
        nextDrafts[item.id] = {
          status: item.status,
          staff_notes: item.staff_notes,
        };
      });
      setFeedback(nextFeedback);
      setDrafts(nextDrafts);
      setError("");
    } catch (loadError) {
      setError(messageFromError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchManagedFeedback()
      .then((nextFeedback) => {
        if (!active) {
          return;
        }
        const nextDrafts: Record<
          number,
          { status: FeedbackStatus; staff_notes: string }
        > = {};
        nextFeedback.forEach((item) => {
          nextDrafts[item.id] = {
            status: item.status,
            staff_notes: item.staff_notes,
          };
        });
        setFeedback(nextFeedback);
        setDrafts(nextDrafts);
        setError("");
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(messageFromError(loadError));
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
  }, []);

  function updateDraft(
    item: ManagedFeedback,
    field: "status" | "staff_notes",
    value: string,
  ) {
    setDrafts((current) => ({
      ...current,
      [item.id]: {
        status: current[item.id]?.status ?? item.status,
        staff_notes: current[item.id]?.staff_notes ?? item.staff_notes,
        [field]: value,
      },
    }));
  }

  async function saveFeedback(item: ManagedFeedback) {
    const draft = drafts[item.id] ?? {
      status: item.status,
      staff_notes: item.staff_notes,
    };
    setPendingId(item.id);
    setNotice(null);
    try {
      await updateManagedFeedback(item.id, draft);
      setNotice({ text: "Feedback updated.", error: false });
      await refresh();
    } catch (saveError) {
      setNotice({ text: messageFromError(saveError), error: true });
    } finally {
      setPendingId(null);
    }
  }

  return (
    <section className="panel-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Private customer messages</p>
          <h2>Feedback inbox</h2>
        </div>
        <button
          className="button button-secondary"
          onClick={() => {
            setLoading(true);
            void refresh();
          }}
        >
          Refresh
        </button>
      </div>
      <p className="muted">
        Feedback and contact details are available only to authorized staff.
        Up to 100 submissions are loaded at a time.
      </p>
      {error && <p className="notice notice-error">{error}</p>}
      {notice && (
        <p className={`notice ${notice.error ? "notice-error" : "notice-ok"}`}>
          {notice.text}
        </p>
      )}
      <div className="card">
        {loading ? (
          <p className="muted">Loading feedback...</p>
        ) : feedback.length === 0 ? (
          <p className="muted">No feedback has been submitted.</p>
        ) : (
          <div className="product-list">
            {feedback.map((item) => {
              const draft = drafts[item.id] ?? {
                status: item.status,
                staff_notes: item.staff_notes,
              };
              return (
                <article className="product-row" key={item.id}>
                  <div className="product-topline">
                    <div>
                      <p className="eyebrow">{item.category}</p>
                      <h3>{item.name || "Anonymous customer"}</h3>
                      <p className="muted">
                        {item.email || "No contact email"} ·{" "}
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span className="status-pill">{item.status.replace("_", " ")}</span>
                  </div>
                  <p className="review-body">{item.message}</p>
                  <div className="feedback-actions">
                    <label>
                      Status
                      <select
                        onChange={(event) =>
                          updateDraft(item, "status", event.currentTarget.value)
                        }
                        value={draft.status}
                      >
                        <option value="new">New</option>
                        <option value="in_progress">In progress</option>
                        <option value="resolved">Resolved</option>
                      </select>
                    </label>
                    <label>
                      Internal notes
                      <textarea
                        onChange={(event) =>
                          updateDraft(
                            item,
                            "staff_notes",
                            event.currentTarget.value,
                          )
                        }
                        rows={2}
                        value={draft.staff_notes}
                      />
                    </label>
                    <button
                      className="button button-primary"
                      disabled={pendingId === item.id}
                      onClick={() => void saveFeedback(item)}
                    >
                      {pendingId === item.id ? "Saving..." : "Save"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

function App() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [sessionError, setSessionError] = useState("");
  const [activeTab, setActiveTab] = useState<DashboardTab>("catalog");
  const [logoutError, setLogoutError] = useState("");

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        if (error instanceof ApiError && error.status === 403) {
          setUser(null);
        } else {
          setSessionError(messageFromError(error));
        }
      })
      .finally(() => {
        if (active) {
          setCheckingSession(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleLogout() {
    setLogoutError("");
    try {
      await logout();
      setUser(null);
    } catch (error) {
      setLogoutError(messageFromError(error));
    }
  }

  if (checkingSession) {
    return <main className="loading-page">Checking staff session...</main>;
  }

  if (sessionError) {
    return (
      <main className="login-page">
        <section className="login-card">
          <p className="eyebrow">Syntrix Quest</p>
          <h1>Backend unavailable</h1>
          <p className="notice notice-error">{sessionError}</p>
          <button
            className="button button-primary"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>
        </section>
      </main>
    );
  }

  if (!user) {
    return <LoginPanel onLogin={setUser} />;
  }

  if (!user.is_staff) {
    return (
      <main className="login-page">
        <section className="login-card">
          <p className="eyebrow">Syntrix Quest</p>
          <h1>Staff access required</h1>
          <p className="muted">
            This account is not enabled for staff administration.
          </p>
          <button className="button button-secondary" onClick={() => void handleLogout()}>
            Sign out
          </button>
          {logoutError && <p className="notice notice-error">{logoutError}</p>}
        </section>
      </main>
    );
  }

  const sectionOptions: {
    id: DashboardTab;
    label: string;
    permission: string | null;
  }[] = [
    { id: "catalog", label: "Catalog", permission: "catalog.view_product" },
    { id: "inventory", label: "Inventory", permission: "inventory.view_stockbalance" },
    { id: "orders", label: "Orders", permission: "orders.view_order" },
    { id: "reviews", label: "Reviews", permission: "reviews.view_productreview" },
    { id: "feedback", label: "Feedback", permission: "feedback.view_customerfeedback" },
    { id: "analytics", label: "Analytics", permission: null },
  ];
  const visibleTabs = sectionOptions.filter(
    (section) =>
      user.is_superuser
      || section.permission === null
      || user.permissions.includes(section.permission),
  );
  const currentTab =
    visibleTabs.find((section) => section.id === activeTab) ?? visibleTabs[0];

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <a className="brand" href="/">
          Syntrix <span>Quest</span>
        </a>
        <div className="staff-controls">
          <span className="staff-name">{user.username}</span>
          <button className="button button-secondary" onClick={() => void handleLogout()}>
            Sign out
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="dashboard-intro">
          <div>
            <p className="eyebrow">Operations</p>
            <h1>Administration</h1>
            <p className="muted">
              Open the catalog, inventory, order queue, analytics, and customer
              workflows available to your role.
            </p>
          </div>
          {visibleTabs.length > 0 && (
            <nav aria-label="Admin sections" className="tab-list">
              {visibleTabs.map((section) => (
                <button
                  aria-selected={currentTab?.id === section.id}
                  className={currentTab?.id === section.id ? "tab active" : "tab"}
                  key={section.id}
                  onClick={() => setActiveTab(section.id)}
                  role="tab"
                >
                  {section.label}
                </button>
              ))}
            </nav>
          )}
        </div>

        {logoutError && <p className="notice notice-error">{logoutError}</p>}
        {visibleTabs.length === 0 ? (
          <p className="notice notice-error">
            This staff account does not have permissions for an admin section.
          </p>
        ) : currentTab?.id === "catalog" ? (
          <CatalogPanel />
        ) : currentTab?.id === "inventory" ? (
          <InventoryPanel />
        ) : currentTab?.id === "orders" ? (
          <OrderQueuePanel />
        ) : currentTab?.id === "reviews" ? (
          <ReviewsPanel />
        ) : currentTab?.id === "analytics" ? (
          <AnalyticsPanel />
        ) : (
          <FeedbackPanel />
        )}
      </div>
    </main>
  );
}

export default App;
