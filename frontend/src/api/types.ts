export type Crop = "tomato" | "chilli" | "ragi";
export type RiskLevel = "low" | "moderate" | "high";
export type ChatRole = "user" | "assistant" | "system";

export type FarmConfig = {
  name: string;
  location: string;
  lat: number;
  lon: number;
  crop: Crop;
  stage: string;
};

export type Telemetry = {
  temperature_c: number | null;
  humidity_pct: number | null;
  soil_moisture_pct: number | null;
  rainfall_mm: number;
  sunlight_wm2: number | null;
  leaf_wet_days?: number;
  source?: string | null;
};

export type HistoricalRecord = {
  date: string;
  soil_moisture_pct: number;
  air_temperature_c: number;
  humidity_pct: number;
  sunlight_wm2: number | null;
  rainfall_mm: number;
  leaf_wet_days?: number;
  source?: string;
};

export type MlRisk = {
  risk_pct: number;
  risk_level: RiskLevel;
  risk_bands?: {
    low_max: number;
    moderate_max: number;
  };
  ml_output_code?: number;
};

export type DashboardResponse = {
  status: string;
  generated_at: string;
  location: {
    name: string;
    lat: number;
    lon: number;
  };
  crop: string;
  current_telemetry: Telemetry;
  historical_trends: HistoricalRecord[];
  ml_risk: MlRisk;
  quick_advisory: string;
};

export type HealthResponse = {
  status: "ok" | "degraded" | string;
  timestamp?: string;
  telemetry?: {
    status: string;
    active_providers?: string[];
  };
  ml_engine?: {
    loaded: boolean;
    model_name?: string | null;
    features_count?: number;
  };
  rag_pipeline?: {
    mongodb_configured: boolean;
    llm_provider?: string;
    groq_configured?: boolean;
  };
};

export type ChatHistoryMessage = {
  role: ChatRole;
  content: string;
};

export type ChatRequest = {
  question: string;
  crop: Crop | string;
  lat: number;
  lon: number;
  location: string;
  chat_history: ChatHistoryMessage[];
  session_id?: string;
};

export type StructuredAdvisory = {
  response_mode?: string;
  overview?: string;
  model_interpretation?: string;
  sensor_readings?: unknown[];
  possible_conditions?: string[];
  watch_list?: string[];
  recommendations?: string[];
  uncertainty?: string[];
  next_step?: string;
  documents_used?: string[];
};

export type ChatResponse = {
  schema_version: string;
  session_id: string;
  crop: string;
  location: Record<string, unknown>;
  answer: string;
  structured: StructuredAdvisory | null;
  risk: Record<string, unknown>;
  telemetry: Record<string, unknown>;
  chat_history: ChatHistoryMessage[];
  retrieval_context?: unknown;
};

export type MlPrediction = {
  risk_pct: number;
  risk_label: RiskLevel;
  risk_level: RiskLevel;
  risk_bands?: {
    low_max: number;
    moderate_max: number;
  };
  index_type?: string;
  validated?: boolean;
};

export type MlPredictRequest = {
  device_id: string;
  lat: number;
  lon: number;
  target_date?: string;
  history: {
    date: string;
    soil_moisture_pct: number;
    air_temperature_c: number;
    humidity_pct: number;
    sunlight_wm2?: number | null;
    rainfall_mm: number;
  }[];
};

export type MlPredictResponse = {
  schema_version: string;
  generated_at: string;
  device_id: string;
  location: {
    lat: number;
    lon: number;
  };
  target_date: string;
  prediction: MlPrediction;
  model?: {
    name: string;
    trained_through: string;
  };
  inputs?: unknown[];
  warnings?: string[];
};

export type RiskPoint = {
  date: string;
  risk_pct: number;
  risk_level: RiskLevel;
};
