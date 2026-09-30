import type {
  DocumentItem, HistoryItem, ResearchResponse, TokenResponse, UploadResponse, User,
} from "./types";

const BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "ra_token";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

export const tokenStore = {
  get: () => (typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY)),
  set: (t: string) => window.localStorage.setItem(TOKEN_KEY, t),
  clear: () => window.localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, init: RequestInit = {}, fallback = "Request failed."): Promise<T> {
  const headers = new Headers(init.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Unable to connect to the backend.", 0);
  }

  if (!res.ok) {
    let message = fallback;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") message = body.detail;
      else if (res.status === 422) message = "Please check the values you entered.";
    } catch { /* keep fallback */ }
    if (res.status === 401 && token) {
      tokenStore.clear();
      window.dispatchEvent(new Event("ra:unauthorized"));
      message = "Authentication required.";
    }
    throw new ApiError(message, res.status);
  }
  return (await res.json()) as T;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  baseUrl: BASE,
  register: (email: string, password: string) =>
    request<TokenResponse>("/auth/register", json({ email, password }), "Registration failed."),
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", json({ email, password }), "Sign in failed."),
  logout: () => request<unknown>("/auth/logout", { method: "POST" }).catch(() => undefined),
  me: () => request<User>("/auth/me"),

  documents: () => request<DocumentItem[]>("/documents", {}, "Could not load documents."),
  deleteDocument: (id: number) =>
    request<{ message: string }>(`/documents/${id}`, { method: "DELETE" }, "Could not delete the document."),

  async uploadPdf(file: File): Promise<UploadResponse> {
    const form = new FormData();
    form.append("file", file);
    // The backend reports some validation problems as { error } with HTTP 200.
    const data = await request<UploadResponse & { error?: string }>(
      "/upload-pdf", { method: "POST", body: form }, "PDF upload failed.");
    if (data.error) throw new ApiError(data.error, 400);
    return data;
  },

  history: () => request<HistoryItem[]>("/research-history", {}, "Could not load history."),
  historyItem: (id: number) =>
    request<HistoryItem>(`/research-history/${id}`, {}, "Could not load this research record."),

  async research(question: string, image?: File | null): Promise<ResearchResponse> {
    const form = new FormData();
    form.append("question", question);
    if (image) form.append("file", image);
    const data = await request<ResearchResponse & { error?: string }>(
      "/agentic-research-multimodal", { method: "POST", body: form }, "Research request failed.");
    if (data.error) throw new ApiError(data.error, 400);
    return data;
  },
};
