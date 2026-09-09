const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


export function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}


export function setAccessToken(token: string) {
  localStorage.setItem("access_token", token);
}


export function clearAccessToken() {
  localStorage.removeItem("access_token");
}


async function readErrorMessage(
  response: Response
): Promise<string> {
  let message =
    `API request failed: ${response.status}`;

  try {
    const body = await response.json();

    if (body?.detail) {
      message =
        typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail);
    }
  } catch {
    // Keep default error message.
  }

  return message;
}


async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();

  const headers = new Headers(
    options.headers
  );

  /*
   * Normal API requests use JSON.
   *
   * FormData requests must NOT manually set
   * Content-Type because the browser creates
   * the multipart boundary automatically.
   */
  const isFormData =
    options.body instanceof FormData;

  if (!isFormData) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers,
    }
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response)
    );
  }

  return response.json();
}


export function apiGet<T>(
  endpoint: string
): Promise<T> {
  return apiRequest<T>(
    endpoint,
    {
      method: "GET",
    }
  );
}


export function apiPost<T>(
  endpoint: string,
  body?: unknown
): Promise<T> {
  return apiRequest<T>(
    endpoint,
    {
      method: "POST",
      body:
        body === undefined
          ? undefined
          : JSON.stringify(body),
    }
  );
}


export function apiPostFormData<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  return apiRequest<T>(
    endpoint,
    {
      method: "POST",
      body: formData,
    }
  );
}