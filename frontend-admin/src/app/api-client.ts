import { config } from "@/app/config";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

type RequestOptions = Omit<RequestInit, "body" | "headers"> & {
  body?: unknown;
  headers?: HeadersInit;
  query?: Record<string, string | number | boolean | null | undefined>;
};

const apiBase = `${config.apiUrl.replace(/\/+$/, "")}/api/v1`;

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { query, body, headers, ...init } = options;
  const url = new URL(
    `${apiBase}${path.startsWith("/") ? path : `/${path}`}`,
    window.location.origin,
  );

  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  const requestHeaders = new Headers(headers);
  requestHeaders.set("Accept", "application/json");
  let requestBody: BodyInit | undefined;

  if (body instanceof FormData) {
    requestBody = body;
  } else if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
    requestBody = JSON.stringify(body);
  }

  const response = await fetch(url, {
    ...init,
    credentials: "include",
    headers: requestHeaders,
    body: requestBody,
  });

  if (!response.ok) {
    const responseText = await response.text();
    let detail: unknown = responseText;
    try {
      detail = responseText ? JSON.parse(responseText) : undefined;
    } catch {
      // Le backend peut renvoyer un message texte brut.
    }

    const message =
      typeof detail === "object" && detail && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : responseText || `La requête a échoué (${response.status}).`;
    throw new ApiError(response.status, message, detail);
  }

  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json() as Promise<T>;
  }
  return response.blob() as Promise<T>;
}

export async function apiDownload(
  path: string,
  filename: string,
  query?: RequestOptions["query"],
) {
  const blob = await apiRequest<Blob>(path, { query });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
