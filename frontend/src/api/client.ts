export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

type RequestOptions = RequestInit & {
  token?: string;
};

function getErrorMessage(data: unknown): string | undefined {
  if (!data || typeof data !== "object") {
    return undefined;
  }

  const record = data as Record<string, unknown>;

  if (typeof record.detail === "string") {
    return record.detail;
  }

  if (Array.isArray(record.detail)) {
    const messages = record.detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return undefined;
        }

        const message = (item as Record<string, unknown>).msg;
        return typeof message === "string" ? message : undefined;
      })
      .filter((message): message is string => Boolean(message));

    if (messages.length > 0) {
      return messages.join("، ");
    }
  }

  if (typeof record.message === "string") {
    return record.message;
  }

  return undefined;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { token, headers: suppliedHeaders, ...requestOptions } = options;
  const headers = new Headers(suppliedHeaders);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (
    requestOptions.body !== undefined &&
    !(requestOptions.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...requestOptions,
    headers,
  });

  if (!response.ok) {
    let message = "خطایی در ارتباط با سرور رخ داد.";

    try {
      const data: unknown = await response.json();
      message = getErrorMessage(data) ?? message;
    } catch {
      // ممکن است پاسخ خطا بدنه‌ی JSON نداشته باشد.
    }

    throw new Error(message);
  }

  if (response.status === 204 || response.status === 205) {
    return undefined as T;
  }

  const responseText = await response.text();

  if (!responseText) {
    return undefined as T;
  }

  try {
    return JSON.parse(responseText) as T;
  } catch {
    throw new Error("پاسخ سرور قابل خواندن نیست.");
  }
}