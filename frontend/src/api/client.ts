import type {
  ChatRequest,
  ChatResponse,
  DashboardResponse,
  FarmConfig,
  HealthResponse,
  HistoricalRecord,
  MlPredictRequest,
  MlPredictResponse,
} from "./types";

export const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

export type ApiErrorKind =
  | "network"
  | "timeout"
  | "server"
  | "validation"
  | "degraded";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number;

  constructor(kind: ApiErrorKind, message: string, status = 0) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
};

function kindFromStatus(status: number): ApiErrorKind {
  if (status === 422) return "validation";
  if (status === 503) return "degraded";
  return "server";
}

function messageFromBody(data: unknown, status: number): string {
  if (typeof data === "string" && data.trim()) return data;
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    const detail = record.detail;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object") {
      const detailRecord = detail as Record<string, unknown>;
      if (typeof detailRecord.message === "string") return detailRecord.message;
    }
    if (typeof record.message === "string") return record.message;
  }
  return `Request failed (${status}).`;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? 60_000,
  );

  if (options.signal) {
    if (options.signal.aborted) controller.abort();
    else
      options.signal.addEventListener("abort", () => controller.abort(), {
        once: true,
      });
  }

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });

    const raw = await response.text();
    let data: unknown = null;
    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch {
        data = raw;
      }
    }

    if (!response.ok) {
      throw new ApiError(
        kindFromStatus(response.status),
        messageFromBody(data, response.status),
        response.status,
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError(
        "timeout",
        "The request timed out. The field engine may be waking up.",
      );
    }
    throw new ApiError(
      "network",
      "Could not reach the Sarva Mitra API. Check your connection and API URL.",
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

function query(params: Record<string, string | number>): string {
  return Object.entries(params)
    .map(
      ([key, value]) =>
        `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`,
    )
    .join("&");
}

export function getDashboard(farm: FarmConfig): Promise<DashboardResponse> {
  return apiRequest<DashboardResponse>(
    `/api/dashboard?${query({
      lat: farm.lat,
      lon: farm.lon,
      location: farm.location,
      crop: farm.crop,
    })}`,
    { timeoutMs: 60_000 },
  );
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/health", { timeoutMs: 10_000 });
}

export function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/api/chat", {
    method: "POST",
    body: payload,
    timeoutMs: 90_000,
  });
}

export function getTelemetryHistory(
  farm: FarmConfig,
  days = 20,
): Promise<HistoricalRecord[]> {
  return apiRequest<HistoricalRecord[]>(
    `/api/telemetry/history?${query({
      lat: farm.lat,
      lon: farm.lon,
      days,
    })}`,
    { timeoutMs: 30_000 },
  );
}

export function predictRisk(
  payload: MlPredictRequest,
): Promise<MlPredictResponse> {
  return apiRequest<MlPredictResponse>("/api/ml/predict", {
    method: "POST",
    body: payload,
    timeoutMs: 20_000,
  });
}
