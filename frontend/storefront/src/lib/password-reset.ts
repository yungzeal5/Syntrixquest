const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

type JsonObject = Record<string, unknown>;

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getErrorMessage(value: unknown): string {
  if (!isJsonObject(value)) {
    return "The request could not be completed.";
  }

  if (typeof value.detail === "string") {
    return value.detail;
  }

  for (const [field, errors] of Object.entries(value)) {
    if (typeof errors === "string") {
      return `${field}: ${errors}`;
    }
    if (Array.isArray(errors) && typeof errors[0] === "string") {
      return `${field}: ${errors[0]}`;
    }
  }

  return "The request could not be completed.";
}

async function readJson(response: Response): Promise<JsonObject> {
  const contentType = response.headers.get("content-type") ?? "";
  const payload: unknown = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    throw new Error(getErrorMessage(payload));
  }
  if (!isJsonObject(payload)) {
    throw new Error("The API returned an invalid response.");
  }

  return payload;
}

export async function postPasswordReset(
  path: "password-reset/" | "password-reset/confirm/",
  payload: Record<string, string>,
): Promise<JsonObject> {
  const csrfResponse = await fetch(`${API_BASE_URL}/auth/csrf/`, {
    credentials: "include",
    cache: "no-store",
  });
  const csrfData = await readJson(csrfResponse);
  if (typeof csrfData.csrfToken !== "string") {
    throw new Error("The API did not provide a CSRF token.");
  }

  const response = await fetch(`${API_BASE_URL}/auth/${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfData.csrfToken,
    },
    body: JSON.stringify(payload),
  });

  return readJson(response);
}
