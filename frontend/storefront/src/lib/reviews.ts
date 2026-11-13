const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

type JsonObject = Record<string, unknown>;

export type ProductReview = {
  id: number;
  display_name: string;
  rating: number;
  title: string;
  body: string;
  created_at: string;
};

export type ProductReviewSummary = {
  average_rating: string;
  review_count: number;
};

export type ProductReviewsResponse = {
  summary: ProductReviewSummary;
  reviews: ProductReview[];
};

export type FeedbackSubmission = {
  name: string;
  email: string;
  category: "general" | "website" | "product" | "service";
  message: string;
};

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
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throw new Error(`The API returned an invalid ${key} value.`);
  }
  return value;
}

function parseReview(value: unknown): ProductReview {
  if (!isJsonObject(value)) {
    throw new Error("The API returned an invalid product review.");
  }
  return {
    id: numberField(value, "id"),
    display_name: stringField(value, "display_name"),
    rating: numberField(value, "rating"),
    title: stringField(value, "title"),
    body: stringField(value, "body"),
    created_at: stringField(value, "created_at"),
  };
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

async function get(path: string): Promise<unknown> {
  return readJson(await fetch(`${API_BASE_URL}/${path}`, {
    credentials: "include",
    cache: "no-store",
  }));
}

async function post(path: string, payload: unknown): Promise<unknown> {
  const csrfData = await get("auth/csrf/");
  if (!isJsonObject(csrfData) || typeof csrfData.csrfToken !== "string") {
    throw new Error("The API did not provide a CSRF token.");
  }
  return readJson(await fetch(`${API_BASE_URL}/${path}`, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfData.csrfToken,
    },
    body: JSON.stringify(payload),
  }));
}

export async function fetchProductReviews(
  productSlug: string,
): Promise<ProductReviewsResponse> {
  const encodedSlug = encodeURIComponent(productSlug);
  const [summaryValue, pageValue] = await Promise.all([
    get(`reviews/products/${encodedSlug}/summary/`),
    get(`reviews/products/${encodedSlug}/?page_size=5`),
  ]);
  if (
    !isJsonObject(summaryValue)
    || !isJsonObject(pageValue)
    || !Array.isArray(pageValue.results)
  ) {
    throw new Error("The API returned an invalid review list.");
  }
  return {
    summary: {
      average_rating: stringField(summaryValue, "average_rating"),
      review_count: numberField(summaryValue, "review_count"),
    },
    reviews: pageValue.results.map(parseReview),
  };
}

export async function submitProductReview(
  productSlug: string,
  data: { display_name: string; rating: number; title: string; body: string },
): Promise<void> {
  const encodedSlug = encodeURIComponent(productSlug);
  await post(`reviews/products/${encodedSlug}/`, data);
}

export async function submitFeedback(data: FeedbackSubmission): Promise<void> {
  await post("feedback/", data);
}
