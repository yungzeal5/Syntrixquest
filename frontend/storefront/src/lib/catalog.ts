export type CatalogVariant = {
  id: number;
  label: string;
  sku: string;
  pack_quantity: string;
  pack_unit: string;
  price: string;
  is_default: boolean;
};

export type CatalogProduct = {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: { name: string; slug: string };
  variants: CatalogVariant[];
};

type JsonObject = Record<string, unknown>;

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiredString(record: JsonObject, key: string): string {
  const value = record[key];
  if (typeof value !== "string") {
    throw new Error(`Catalog API returned an invalid ${key} value.`);
  }
  return value;
}

function requiredNumber(record: JsonObject, key: string): number {
  const value = record[key];
  if (typeof value !== "number") {
    throw new Error(`Catalog API returned an invalid ${key} value.`);
  }
  return value;
}

function parseVariant(value: unknown): CatalogVariant {
  if (!isJsonObject(value) || typeof value.is_default !== "boolean") {
    throw new Error("Catalog API returned an invalid product variant.");
  }

  return {
    id: requiredNumber(value, "id"),
    label: requiredString(value, "label"),
    sku: requiredString(value, "sku"),
    pack_quantity: requiredString(value, "pack_quantity"),
    pack_unit: requiredString(value, "pack_unit"),
    price: requiredString(value, "price"),
    is_default: value.is_default,
  };
}

function parseProduct(value: unknown): CatalogProduct {
  if (
    !isJsonObject(value) ||
    !isJsonObject(value.category) ||
    !Array.isArray(value.variants)
  ) {
    throw new Error("Catalog API returned an invalid product.");
  }

  return {
    id: requiredNumber(value, "id"),
    name: requiredString(value, "name"),
    slug: requiredString(value, "slug"),
    description: requiredString(value, "description"),
    category: {
      name: requiredString(value.category, "name"),
      slug: requiredString(value.category, "slug"),
    },
    variants: value.variants.map(parseVariant),
  };
}

export async function fetchCatalog(): Promise<CatalogProduct[]> {
  const response = await fetch(
    `${API_BASE_URL}/catalog/products/?page_size=100`,
    { cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(`Catalog API returned status ${response.status}.`);
  }

  const payload: unknown = await response.json();
  if (!isJsonObject(payload) || !Array.isArray(payload.results)) {
    throw new Error("Catalog API returned an invalid product list.");
  }

  return payload.results.map(parseProduct);
}

export async function fetchCatalogProduct(
  slug: string,
): Promise<CatalogProduct | null> {
  const response = await fetch(
    `${API_BASE_URL}/catalog/products/${encodeURIComponent(slug)}/`,
    { cache: "no-store" },
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Catalog API returned status ${response.status}.`);
  }
  return parseProduct(await response.json());
}
