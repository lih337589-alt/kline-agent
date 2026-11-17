const DEFAULT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000";

const PUBLIC_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ||
  DEFAULT_PUBLIC_API_BASE_URL;

const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL?.replace(/\/+$/, "") ||
  PUBLIC_API_BASE_URL;

export const API_BASE_URL =
  typeof window === "undefined"
    ? INTERNAL_API_BASE_URL
    : PUBLIC_API_BASE_URL;

export type StockRead = {
  id: number;
  symbol: string;
  name: string;
  exchange: string | null;
  industry: string | null;
  created_at: string;
};

export type PriceRead = {
  id: number;
  timestamp: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
  source: string;
  created_at: string;
};

export type StockPriceSeries = {
  symbol: string;
  count: number;
  latest_timestamp: string | null;
  sources: string[];
  prices: PriceRead[];
};

export type AgentResult = {
  summary: string;
  positives: string[];
  negatives: string[];
  evidence_ids: string[];
  confidence: number;
  limitations: string[];
};

export type BullClaim = {
  claim_id: string;
  claim: string;
  rationale: string;
  evidence_ids: string[];
  evidence_insufficient: boolean;
};

export type BearRebuttal = {
  rebuttal_id: string;
  bull_claim_id: string;
  counter_argument: string;
  evidence_ids: string[];
  evidence_insufficient: boolean;
};

export type DebateResult = {
  bull_claims: BullClaim[];
  bear_rebuttals: BearRebuttal[];
  unresolved_questions: string[];
};

export type CrossIssueCategory =
  | "date_conflict"
  | "evidence_gap"
  | "logic_gap"
  | "metric_mismatch"
  | "data_quality"
  | "other";

export type IssueSeverity =
  | "low"
  | "medium"
  | "high";

export type CrossIssue = {
  issue_id: string;
  category: CrossIssueCategory;
  severity: IssueSeverity;
  description: string;
  related_ids: string[];
  evidence_ids: string[];
  evidence_insufficient: boolean;
};

export type CrossExamResult = {
  summary: string;
  issues: CrossIssue[];
  unresolved_questions: string[];
};

export type JudgeDecision =
  | "accepted"
  | "rejected"
  | "partially_accepted"
  | "uncertain";

export type JudgePointAssessment = {
  point_id: string;
  decision: JudgeDecision;
  reason: string;
  evidence_ids: string[];
  evidence_insufficient: boolean;
};

export type JudgeResult = {
  overall_view: string;
  key_drivers: string[];
  key_risks: string[];
  disputes: string[];
  point_assessments: JudgePointAssessment[];
  confidence: number;
  data_freshness: string;
  limitations: string[];
};

export type ReportPayload = {
  symbol: string;
  company_name: string;
  trace_id: string;
  executive_summary: string;
  fundamental: AgentResult;
  valuation: AgentResult;
  technical: AgentResult;
  sentiment: AgentResult;
  risk: AgentResult;
  debate: DebateResult;
  cross_exam: CrossExamResult;
  judgment: JudgeResult;
  sources: string[];
  agent_run_ids: number[];
};

export type AnalysisRequest = {
  symbol: string;
  use_cache: boolean;
};

export type AnalysisCreatedResponse = {
  report_id: number;
  trace_id: string;
  symbol: string;
  status: string;
};

export type ReportRead = {
  id: number;
  stock_id: number;
  symbol: string;
  trace_id: string;
  title: string;
  status: string;
  source: string;
  report: ReportPayload;
  created_at: string;
};

export type RiskSeverity =
  | "low"
  | "medium"
  | "high";


export type RiskExplanation = {
  severity: RiskSeverity;
  reason: string;
  impact_path: string[];
  uncertainty: string;
  suggested_attention: string[];
};


export type RiskAlertRead = {
  id: number;
  stock_id: number;
  symbol: string;
  alert_type: string;
  severity: RiskSeverity;
  message: string;
  source: string;
  event_time: string;
  created_at: string;
  explanation: RiskExplanation | null;
};


export type RiskAlertListResponse = {
  count: number;
  alerts: RiskAlertRead[];
};


export class ApiRequestError extends Error {
  status: number | null;

  constructor(
    message: string,
    status: number | null = null,
  ) {
    super(message);

    this.name = "ApiRequestError";
    this.status = status;
  }
}

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/")
    ? path
    : `/${path}`;

  return `${API_BASE_URL}${normalizedPath}`;
}

async function requestJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(
      apiUrl(path),
      {
        cache: "no-store",
        ...init,
      },
    );
  } catch {
    throw new ApiRequestError(
      "Unable to reach the backend API.",
    );
  }

  if (!response.ok) {
    let message =
      `API request failed with status ${response.status}.`;

    try {
      const payload = (await response.json()) as {
        detail?: unknown;
        error?: {
          message?: unknown;
        };
      };

      if (
        typeof payload.error?.message === "string"
      ) {
        message = payload.error.message;
      } else if (
        typeof payload.detail === "string"
      ) {
        message = payload.detail;
      }
    } catch {
      // Keep the generic HTTP error message.
    }

    throw new ApiRequestError(
      message,
      response.status,
    );
  }

  return (await response.json()) as T;
}

export async function getStock(
  symbol: string,
): Promise<StockRead> {
  const normalizedSymbol =
    encodeURIComponent(
      symbol.trim().toUpperCase(),
    );

  return requestJson<StockRead>(
    `/api/stocks/${normalizedSymbol}`,
  );
}

export async function getStockPrices(
  symbol: string,
  limit = 120,
): Promise<StockPriceSeries> {
  const normalizedSymbol =
    encodeURIComponent(
      symbol.trim().toUpperCase(),
    );

  return requestJson<StockPriceSeries>(
    `/api/stocks/${normalizedSymbol}/prices?limit=${limit}`,
  );
}

export async function getReport(
  reportId: number,
): Promise<ReportRead> {
  return requestJson<ReportRead>(
    `/api/reports/${reportId}`,
  );
}

export async function createAnalysis(
  payload: AnalysisRequest,
): Promise<AnalysisCreatedResponse> {
  return requestJson<AnalysisCreatedResponse>(
    "/api/analyses",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(
        payload,
      ),
    },
  );
}

export async function getRiskAlerts(
  symbol?: string,
  limit = 20,
): Promise<RiskAlertListResponse> {
  const params =
    new URLSearchParams();

  if (symbol) {
    params.set(
      "symbol",
      symbol
        .trim()
        .toUpperCase(),
    );
  }

  params.set(
    "limit",
    String(limit),
  );

  return requestJson<RiskAlertListResponse>(
    `/api/alerts?${params.toString()}`,
  );
}
