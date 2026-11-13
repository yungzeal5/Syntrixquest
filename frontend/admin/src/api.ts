const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

type JsonObject = Record<string, unknown>;

export type SessionUser = {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_superuser: boolean;
  permissions: string[];
};

export type Category = {
  id: number;
  name: string;
  slug: string;
};

export type ProductVariant = {
  id: number;
  product: string;
  label: string;
  sku: string;
  pack_quantity: string;
  pack_unit: string;
  price: string;
  is_active: boolean;
  is_default: boolean;
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
  category: Category;
  variants: ProductVariant[];
};

export type StockBalance = {
  variant_id: number;
  sku: string;
  product_name: string;
  variant_label: string;
  quantity_on_hand: number;
  updated_at: string;
};

export type StockMovement = {
  id: number;
  variant_id: number;
  variant_sku: string;
  movement_type: string;
  quantity: number;
  reason: string;
  created_by: string | null;
  created_at: string;
};

export type ProductReviewStatus = "pending" | "approved" | "rejected";

export type ManagedProductReview = {
  id: number;
  product_name: string;
  display_name: string;
  rating: number;
  title: string;
  body: string;
  status: ProductReviewStatus;
  moderated_by: string | null;
  moderated_at: string | null;
  created_at: string;
};

export type FeedbackStatus = "new" | "in_progress" | "resolved";

export type ManagedFeedback = {
  id: number;
  name: string;
  email: string;
  category: string;
  message: string;
  status: FeedbackStatus;
  staff_notes: string;
  submitted_by: string | null;
  created_at: string;
  updated_at: string;
};

export type ManagedOrderStatus = "pending_payment" | "paid" | "cancelled";

export type ManagedOrderItem = {
  product_name: string;
  variant_label: string;
  sku: string;
  quantity: number;
};

export type ManagedOrder = {
  public_id: string;
  status: ManagedOrderStatus;
  created_at: string;
  items: ManagedOrderItem[];
};

export type OperationsOverview = {
  catalog: {
    active_products: number;
    active_variants: number;
  };
  inventory: {
    packages_on_hand: number;
    packages_reserved: number;
    packages_available: number;
  };
  orders: {
    pending_payment: number;
    paid: number;
    cancelled: number;
  };
  reviews: {
    pending: number;
    approved: number;
    rejected: number;
    average_approved_rating: string;
  };
  feedback: {
    new: number;
    in_progress: number;
    resolved: number;
  };
};

export class ApiError extends Error {
  readonly status: number;

  constructor(
    message: string,
    status: number,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringField(record: JsonObject, key: string): string {
  const value = record[key];
  if (typeof value !== "string") {
    throw new Error(`The API returned an invalid ${key} value.`);
  }
  return value;
}

function numberField(record: JsonObject, key: string): number {
  const value = record[key];
  if (typeof value !== "number") {
    throw new Error(`The API returned an invalid ${key} value.`);
  }
  return value;
}

function booleanField(record: JsonObject, key: string): boolean {
  const value = record[key];
  if (typeof value !== "boolean") {
    throw new Error(`The API returned an invalid ${key} value.`);
  }
  return value;
}

function errorMessage(payload: unknown): string {
  if (!isJsonObject(payload)) {
    return "The request could not be completed.";
  }
  if (typeof payload.detail === "string") {
    return payload.detail;
  }
  for (const [field, errors] of Object.entries(payload)) {
    if (typeof errors === "string") {
      return `${field}: ${errors}`;
    }
    if (Array.isArray(errors) && typeof errors[0] === "string") {
      return `${field}: ${errors[0]}`;
    }
  }
  return "The request could not be completed.";
}

async function readResponse(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get("content-type") ?? "";
  const payload: unknown = contentType.includes("application/json")
    ? await response.json()
    : null;
  if (!response.ok) {
    throw new ApiError(errorMessage(payload), response.status);
  }
  return payload;
}

async function request(
  path: string,
  init: RequestInit = {},
): Promise<unknown> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
    const csrfResponse = await fetch(`${API_BASE_URL}/auth/csrf/`, {
      credentials: "include",
      cache: "no-store",
    });
    const csrfPayload = await readResponse(csrfResponse);
    if (!isJsonObject(csrfPayload) || typeof csrfPayload.csrfToken !== "string") {
      throw new Error("The API did not provide a CSRF token.");
    }
    headers.set("X-CSRFToken", csrfPayload.csrfToken);
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}/${path}`, {
    ...init,
    method,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  return readResponse(response);
}

function parseUser(value: unknown): SessionUser {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid session user.");
  }
  if (
    !Array.isArray(value.permissions)
    || !value.permissions.every((permission) => typeof permission === "string")
  ) {
    throw new Error("The API returned invalid user permissions.");
  }
  return {
    id: numberField(value, "id"),
    username: stringField(value, "username"),
    email: stringField(value, "email"),
    is_staff: booleanField(value, "is_staff"),
    is_superuser: booleanField(value, "is_superuser"),
    permissions: value.permissions,
  };
}

function parseCategory(value: unknown): Category {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid category.");
  }
  return {
    id: numberField(value, "id"),
    name: stringField(value, "name"),
    slug: stringField(value, "slug"),
  };
}

function parseVariant(value: unknown): ProductVariant {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid product variant.");
  }
  return {
    id: numberField(value, "id"),
    product: stringField(value, "product"),
    label: stringField(value, "label"),
    sku: stringField(value, "sku"),
    pack_quantity: stringField(value, "pack_quantity"),
    pack_unit: stringField(value, "pack_unit"),
    price: stringField(value, "price"),
    is_active: booleanField(value, "is_active"),
    is_default: booleanField(value, "is_default"),
  };
}

function parseProduct(value: unknown): Product {
  if (!isJsonObject(value) || !Array.isArray(value.variants)) {
    throw new Error("The API returned an invalid product.");
  }
  return {
    id: numberField(value, "id"),
    name: stringField(value, "name"),
    slug: stringField(value, "slug"),
    description: stringField(value, "description"),
    is_active: booleanField(value, "is_active"),
    category: parseCategory(value.category),
    variants: value.variants.map(parseVariant),
  };
}

function parsePage<T>(
  value: unknown,
  parseItem: (item: unknown) => T,
): T[] {
  if (!isJsonObject(value) || !Array.isArray(value.results)) {
    throw new Error("The API returned an invalid paginated response.");
  }
  return value.results.map(parseItem);
}

function parseBalance(value: unknown): StockBalance {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid stock balance.");
  }
  return {
    variant_id: numberField(value, "variant_id"),
    sku: stringField(value, "sku"),
    product_name: stringField(value, "product_name"),
    variant_label: stringField(value, "variant_label"),
    quantity_on_hand: numberField(value, "quantity_on_hand"),
    updated_at: stringField(value, "updated_at"),
  };
}

function parseMovement(value: unknown): StockMovement {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid stock movement.");
  }
  const createdBy = value.created_by;
  if (createdBy !== null && typeof createdBy !== "string") {
    throw new Error("The API returned an invalid stock movement actor.");
  }
  return {
    id: numberField(value, "id"),
    variant_id: numberField(value, "variant_id"),
    variant_sku: stringField(value, "variant_sku"),
    movement_type: stringField(value, "movement_type"),
    quantity: numberField(value, "quantity"),
    reason: stringField(value, "reason"),
    created_by: createdBy,
    created_at: stringField(value, "created_at"),
  };
}

function parseReview(value: unknown): ManagedProductReview {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid product review.");
  }
  const status = stringField(value, "status");
  if (status !== "pending" && status !== "approved" && status !== "rejected") {
    throw new Error("The API returned an invalid review status.");
  }
  const moderatedBy = value.moderated_by;
  if (moderatedBy !== null && typeof moderatedBy !== "string") {
    throw new Error("The API returned an invalid review moderator.");
  }
  const moderatedAt = value.moderated_at;
  if (moderatedAt !== null && typeof moderatedAt !== "string") {
    throw new Error("The API returned an invalid moderation timestamp.");
  }
  return {
    id: numberField(value, "id"),
    product_name: stringField(value, "product_name"),
    display_name: stringField(value, "display_name"),
    rating: numberField(value, "rating"),
    title: stringField(value, "title"),
    body: stringField(value, "body"),
    status,
    moderated_by: moderatedBy,
    moderated_at: moderatedAt,
    created_at: stringField(value, "created_at"),
  };
}

function parseFeedback(value: unknown): ManagedFeedback {
  if (!isJsonObject(value)) {
    throw new Error("The API returned invalid customer feedback.");
  }
  const status = stringField(value, "status");
  if (status !== "new" && status !== "in_progress" && status !== "resolved") {
    throw new Error("The API returned an invalid feedback status.");
  }
  const submittedBy = value.submitted_by;
  if (submittedBy !== null && typeof submittedBy !== "string") {
    throw new Error("The API returned an invalid feedback submitter.");
  }
  return {
    id: numberField(value, "id"),
    name: stringField(value, "name"),
    email: stringField(value, "email"),
    category: stringField(value, "category"),
    message: stringField(value, "message"),
    status,
    staff_notes: stringField(value, "staff_notes"),
    submitted_by: submittedBy,
    created_at: stringField(value, "created_at"),
    updated_at: stringField(value, "updated_at"),
  };
}

function parseManagedOrder(value: unknown): ManagedOrder {
  if (!isJsonObject(value) || !Array.isArray(value.items)) {
    throw new Error("The API returned an invalid order.");
  }
  const status = stringField(value, "status");
  if (
    status !== "pending_payment"
    && status !== "paid"
    && status !== "cancelled"
  ) {
    throw new Error("The API returned an invalid order status.");
  }
  return {
    public_id: stringField(value, "public_id"),
    status,
    created_at: stringField(value, "created_at"),
    items: value.items.map((item) => {
      if (!isJsonObject(item)) {
        throw new Error("The API returned an invalid order item.");
      }
      return {
        product_name: stringField(item, "product_name"),
        variant_label: stringField(item, "variant_label"),
        sku: stringField(item, "sku"),
        quantity: numberField(item, "quantity"),
      };
    }),
  };
}

function parseOverviewSection(value: unknown, section: string): JsonObject {
  if (!isJsonObject(value)) {
    throw new Error(`The API returned invalid ${section} analytics.`);
  }
  return value;
}

function parseOperationsOverview(value: unknown): OperationsOverview {
  const overview = parseOverviewSection(value, "operations");
  const catalog = parseOverviewSection(overview.catalog, "catalog");
  const inventory = parseOverviewSection(overview.inventory, "inventory");
  const orders = parseOverviewSection(overview.orders, "orders");
  const reviews = parseOverviewSection(overview.reviews, "reviews");
  const feedback = parseOverviewSection(overview.feedback, "feedback");

  return {
    catalog: {
      active_products: numberField(catalog, "active_products"),
      active_variants: numberField(catalog, "active_variants"),
    },
    inventory: {
      packages_on_hand: numberField(inventory, "packages_on_hand"),
      packages_reserved: numberField(inventory, "packages_reserved"),
      packages_available: numberField(inventory, "packages_available"),
    },
    orders: {
      pending_payment: numberField(orders, "pending_payment"),
      paid: numberField(orders, "paid"),
      cancelled: numberField(orders, "cancelled"),
    },
    reviews: {
      pending: numberField(reviews, "pending"),
      approved: numberField(reviews, "approved"),
      rejected: numberField(reviews, "rejected"),
      average_approved_rating: stringField(
        reviews,
        "average_approved_rating",
      ),
    },
    feedback: {
      new: numberField(feedback, "new"),
      in_progress: numberField(feedback, "in_progress"),
      resolved: numberField(feedback, "resolved"),
    },
  };
}

function jsonBody(value: JsonObject): string {
  return JSON.stringify(value);
}

export async function getCurrentUser(): Promise<SessionUser> {
  return parseUser(await request("auth/me/"));
}

export async function login(
  username: string,
  password: string,
): Promise<SessionUser> {
  return parseUser(
    await request("auth/login/", {
      method: "POST",
      body: jsonBody({ username, password }),
    }),
  );
}

export async function logout(): Promise<void> {
  await request("auth/logout/", { method: "POST", body: "{}" });
}

export async function fetchCategories(): Promise<Category[]> {
  return parsePage(
    await request("catalog/categories/?page_size=100"),
    parseCategory,
  );
}

export async function fetchProducts(): Promise<Product[]> {
  return parsePage(
    await request("catalog/products/?page_size=100"),
    parseProduct,
  );
}

export async function createCategory(data: {
  name: string;
  slug: string;
}): Promise<void> {
  await request("catalog/categories/", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function createProduct(data: {
  name: string;
  slug: string;
  description: string;
  category_id: number;
}): Promise<void> {
  await request("catalog/products/", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function createVariant(data: {
  product_id: number;
  label: string;
  sku: string;
  pack_quantity: string;
  pack_unit: string;
  price: string;
}): Promise<void> {
  await request("catalog/variants/", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function setProductActive(
  slug: string,
  isActive: boolean,
): Promise<void> {
  await request(`catalog/products/${encodeURIComponent(slug)}/`, {
    method: "PATCH",
    body: jsonBody({ is_active: isActive }),
  });
}

export async function setVariantActive(
  id: number,
  isActive: boolean,
): Promise<void> {
  await request(`catalog/variants/${id}/`, {
    method: "PATCH",
    body: jsonBody({ is_active: isActive }),
  });
}

export async function fetchVariants(): Promise<ProductVariant[]> {
  return parsePage(
    await request("catalog/variants/?page_size=100"),
    parseVariant,
  );
}

export async function fetchBalances(): Promise<StockBalance[]> {
  return parsePage(
    await request("inventory/balances/?page_size=100"),
    parseBalance,
  );
}

export async function fetchMovements(): Promise<StockMovement[]> {
  return parsePage(
    await request("inventory/movements/?page_size=100"),
    parseMovement,
  );
}

export async function recordMovement(data: {
  variant_id: number;
  movement_type: string;
  quantity: number;
  reason: string;
}): Promise<void> {
  await request("inventory/movements/", {
    method: "POST",
    body: jsonBody(data),
  });
}

export async function fetchManagedReviews(): Promise<ManagedProductReview[]> {
  return parsePage(
    await request("reviews/manage/?page_size=100"),
    parseReview,
  );
}

export async function setProductReviewStatus(
  id: number,
  status: ProductReviewStatus,
): Promise<void> {
  await request(`reviews/manage/${id}/`, {
    method: "PATCH",
    body: jsonBody({ status }),
  });
}

export async function fetchManagedFeedback(): Promise<ManagedFeedback[]> {
  return parsePage(
    await request("feedback/manage/?page_size=100"),
    parseFeedback,
  );
}

export async function updateManagedFeedback(
  id: number,
  data: { status: FeedbackStatus; staff_notes: string },
): Promise<void> {
  await request(`feedback/manage/${id}/`, {
    method: "PATCH",
    body: jsonBody(data),
  });
}

export async function fetchOperationsOverview(): Promise<OperationsOverview> {
  return parseOperationsOverview(await request("analytics/overview/"));
}

export async function fetchManagedOrders(): Promise<ManagedOrder[]> {
  return parsePage(
    await request("orders/manage/?page_size=100"),
    parseManagedOrder,
  );
}
