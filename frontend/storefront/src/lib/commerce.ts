const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

type JsonObject = Record<string, unknown>;

export type CartItem = {
  id: number;
  variant_id: number;
  product_name: string;
  variant_label: string;
  sku: string;
  pack_quantity: string;
  pack_unit: string;
  unit_price: string;
  quantity: number;
  line_total: string;
  quantity_available: number;
};

export type Cart = {
  items: CartItem[];
  items_subtotal: string;
};

export type ShippingDetails = {
  contact_email: string;
  recipient_name: string;
  phone_number: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  region: string;
  postal_code: string;
  country_code: string;
  delivery_instructions: string;
};

export type OrderItem = {
  product_name: string;
  variant_label: string;
  sku: string;
  pack_quantity: string;
  pack_unit: string;
  unit_price: string;
  quantity: number;
  line_total: string;
};

export type Order = ShippingDetails & {
  public_id: string;
  status: "pending_payment" | "paid" | "cancelled";
  items_subtotal: string;
  items: OrderItem[];
  paid_at: string | null;
  cancelled_at: string | null;
  created_at: string;
};

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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

function stringField(record: JsonObject, key: string): string {
  const value = record[key];
  if (typeof value !== "string") {
    throw new Error(`The API returned an invalid ${key} value.`);
  }
  return value;
}

function numberField(record: JsonObject, key: string): number {
  const value = record[key];
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throw new Error(`The API returned an invalid ${key} value.`);
  }
  return value;
}

function nullableStringField(record: JsonObject, key: string): string | null {
  const value = record[key];
  if (value !== null && typeof value !== "string") {
    throw new Error(`The API returned an invalid ${key} value.`);
  }
  return value;
}

function parseCartItem(value: unknown): CartItem {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid cart item.");
  }
  return {
    id: numberField(value, "id"),
    variant_id: numberField(value, "variant_id"),
    product_name: stringField(value, "product_name"),
    variant_label: stringField(value, "variant_label"),
    sku: stringField(value, "sku"),
    pack_quantity: stringField(value, "pack_quantity"),
    pack_unit: stringField(value, "pack_unit"),
    unit_price: stringField(value, "unit_price"),
    quantity: numberField(value, "quantity"),
    line_total: stringField(value, "line_total"),
    quantity_available: numberField(value, "quantity_available"),
  };
}

function parseCart(value: unknown): Cart {
  if (!isJsonObject(value) || !Array.isArray(value.items)) {
    throw new Error("The API returned an invalid cart.");
  }
  return {
    items: value.items.map(parseCartItem),
    items_subtotal: stringField(value, "items_subtotal"),
  };
}

function parseOrderItem(value: unknown): OrderItem {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid order item.");
  }
  return {
    product_name: stringField(value, "product_name"),
    variant_label: stringField(value, "variant_label"),
    sku: stringField(value, "sku"),
    pack_quantity: stringField(value, "pack_quantity"),
    pack_unit: stringField(value, "pack_unit"),
    unit_price: stringField(value, "unit_price"),
    quantity: numberField(value, "quantity"),
    line_total: stringField(value, "line_total"),
  };
}

function parseOrder(value: unknown): Order {
  if (
    !isJsonObject(value)
    || !Array.isArray(value.items)
    || (
      value.status !== "pending_payment"
      && value.status !== "paid"
      && value.status !== "cancelled"
    )
  ) {
    throw new Error("The API returned an invalid order.");
  }
  return {
    public_id: stringField(value, "public_id"),
    status: value.status,
    contact_email: stringField(value, "contact_email"),
    recipient_name: stringField(value, "recipient_name"),
    phone_number: stringField(value, "phone_number"),
    address_line_1: stringField(value, "address_line_1"),
    address_line_2: stringField(value, "address_line_2"),
    city: stringField(value, "city"),
    region: stringField(value, "region"),
    postal_code: stringField(value, "postal_code"),
    country_code: stringField(value, "country_code"),
    delivery_instructions: stringField(value, "delivery_instructions"),
    items_subtotal: stringField(value, "items_subtotal"),
    items: value.items.map(parseOrderItem),
    paid_at: nullableStringField(value, "paid_at"),
    cancelled_at: nullableStringField(value, "cancelled_at"),
    created_at: stringField(value, "created_at"),
  };
}

async function readJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  const payload: unknown = contentType.includes("application/json")
    ? await response.json()
    : null;
  if (!response.ok) {
    throw new Error(errorMessage(payload));
  }
  return payload;
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/${path}`, {
    ...init,
    credentials: "include",
    cache: "no-store",
  });
  return readJson(response);
}

async function postJson(path: string, payload: unknown): Promise<unknown> {
  const csrfData = await request("auth/csrf/");
  if (!isJsonObject(csrfData) || typeof csrfData.csrfToken !== "string") {
    throw new Error("The API did not provide a CSRF token.");
  }
  return request(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfData.csrfToken,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchCart(): Promise<Cart> {
  return parseCart(await request("cart/"));
}

export async function addCartItem(variantId: number): Promise<Cart> {
  return parseCart(
    await postJson("cart/", { variant_id: variantId, quantity: 1 }),
  );
}

export async function updateCartItem(
  itemId: number,
  quantity: number,
): Promise<Cart> {
  const csrfData = await request("auth/csrf/");
  if (!isJsonObject(csrfData) || typeof csrfData.csrfToken !== "string") {
    throw new Error("The API did not provide a CSRF token.");
  }
  return parseCart(await request(`cart/items/${itemId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfData.csrfToken,
    },
    body: JSON.stringify({ quantity }),
  }));
}

export async function removeCartItem(itemId: number): Promise<Cart> {
  const csrfData = await request("auth/csrf/");
  if (!isJsonObject(csrfData) || typeof csrfData.csrfToken !== "string") {
    throw new Error("The API did not provide a CSRF token.");
  }
  await request(`cart/items/${itemId}/`, {
    method: "DELETE",
    headers: { "X-CSRFToken": csrfData.csrfToken },
  });
  return fetchCart();
}

export async function placeOrder(details: ShippingDetails): Promise<Order> {
  return parseOrder(await postJson("checkout/", details));
}

export async function fetchOrder(publicId: string): Promise<Order> {
  return parseOrder(
    await request(`orders/${encodeURIComponent(publicId)}/`),
  );
}

export async function cancelOrder(publicId: string): Promise<Order> {
  return parseOrder(
    await postJson(`orders/${encodeURIComponent(publicId)}/cancel/`, {}),
  );
}
