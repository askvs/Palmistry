const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor({ code, message, requestId, status, fields }) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.requestId = requestId;
    this.status = status;
    this.fields = fields || [];
  }
}

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export function clearAccessToken() {
  accessToken = null;
}

let refreshInFlight = null;

// Shared refresh so concurrent callers reuse one request.
export function requestRefresh() {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      const response = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        clearAccessToken();
        let payload = null;
        try {
          payload = await response.json();
        } catch {
          payload = null;
        }
        throw toApiError(response, payload);
      }
      const payload = await response.json();
      setAccessToken(payload.access_token);
      return payload;
    })().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

function refreshAccessToken() {
  return requestRefresh().then(
    () => true,
    () => false,
  );
}

function shouldRetryAfterRefresh(path, response) {
  return (
    response.status === 401 &&
    accessToken &&
    !path.startsWith("/api/v1/auth/")
  );
}

async function performRequest(path, init) {
  const response = await fetch(`${BASE_URL}${path}`, init);
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  return { response, payload };
}

function toApiError(response, payload) {
  // Fall back when payload is null or malformed.
  const errorCode = payload?.code || `HTTP_${response.status}`;
  const errorMessage = payload?.message || response.statusText || "Request failed";

  return new ApiError({
    code: errorCode,
    message: errorMessage,
    requestId: payload?.request_id,
    status: response.status,
    fields: payload?.fields,
  });
}

export async function apiFetch(path, { method = "GET", body, headers, signal } = {}) {
  const buildInit = () => ({
    method,
    credentials: "include",
    headers: {
      ...(body !== undefined && !(body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
    signal,
  });

  let { response, payload } = await performRequest(path, buildInit());
  if (shouldRetryAfterRefresh(path, response) && (await refreshAccessToken())) {
    ({ response, payload } = await performRequest(path, buildInit()));
  }

  if (!response.ok) {
    throw toApiError(response, payload);
  }
  return payload;
}

function extractErrorMessage(payload, response) {
  if (!payload) return response.statusText || "Request failed";
  if (typeof payload.message === "string" && payload.message) return payload.message;
  if (typeof payload.detail === "string" && payload.detail) return payload.detail;
  if (payload.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message) {
      return payload.detail.message;
    }
    if (typeof payload.detail.code === "string") {
      const code = payload.detail.code;
      const pretty = code.toLowerCase().replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
      return payload.detail.message || pretty;
    }
  }
  if (typeof payload.code === "string" && !payload.message) {
    return payload.code.toLowerCase().replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
  }
  return response.statusText || "Request failed";
}

function extractErrorCode(payload, response) {
  if (payload?.code) return payload.code;
  if (payload?.detail?.code) return payload.detail.code;
  if (payload?.err) return payload.err;
  return `HTTP_${response.status}`;
}

export function parseContentDisposition(header) {
  if (!header) return null;
  // Extended value first, then quoted filename.
  const star = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(header);
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1].replace(/"/g, "").trim());
    } catch {
      return star[1].replace(/"/g, "").trim();
    }
  }
  const quoted = /filename\s*=\s*"([^"]+)"/i.exec(header);
  if (quoted?.[1]) return quoted[1];
  const bare = /filename\s*=\s*([^;]+)/i.exec(header);
  return bare?.[1]?.trim() || null;
}

export async function apiBlob(path, { signal } = {}) {
  const buildInit = () => ({
    method: "GET",
    credentials: "include",
    headers: {
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    signal,
  });

  let response = await fetch(`${BASE_URL}${path}`, buildInit());

  // Retry once after silent refresh, mirroring apiFetch.
  if (shouldRetryAfterRefresh(path, response) && (await refreshAccessToken())) {
    response = await fetch(`${BASE_URL}${path}`, buildInit());
  }

  if (!response.ok) {
    let payload = null;
    try {
      payload = await response.clone().json();
    } catch {
      payload = null;
    }
    throw new ApiError({
      code: extractErrorCode(payload, response),
      message: extractErrorMessage(payload, response),
      requestId: payload?.request_id || payload?.detail?.request_id,
      status: response.status,
    });
  }
  const blob = await response.blob();
  return {
    blob,
    filename: parseContentDisposition(response.headers.get("content-disposition")),
    contentType: response.headers.get("content-type"),
  };
}

export const api = {
  get: (path, options) => apiFetch(path, { ...options, method: "GET" }),
  post: (path, body, options) => apiFetch(path, { ...options, method: "POST", body }),
  put: (path, body, options) => apiFetch(path, { ...options, method: "PUT", body }),
  patch: (path, body, options) => apiFetch(path, { ...options, method: "PATCH", body }),
  delete: (path, options) => apiFetch(path, { ...options, method: "DELETE" }),
};
