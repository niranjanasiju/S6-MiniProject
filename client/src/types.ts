export interface PredictRequest {
  new_drug: string;
  current_drugs: string[];
  age?: number | null;
  gender?: string | null;
}

export interface PolypharmacySideEffect {
  effect: string;
  probability: number;
  severity: number;
}

export interface AIExplanation {
  what_is_it: string;
  what_did_we_find: string;
  side_effects_to_watch: string;
  safe_usage_tips: string;
  when_to_call_doctor: string;
}

export interface PredictionPair {
  pair: string;
  safety_score?: number;
  risk_tier?: string;
  side_effects?: PolypharmacySideEffect[];
  ai_explanation?: AIExplanation;
  error?: string;
}

export interface PredictResponse {
  new_drug: string;
  current_drugs: string[];
  overall_verdict: string;
  overall_score: number;
  pairs: PredictionPair[];
}

export interface ADRRequest {
  drug_name: string;
  threshold?: number;
}

export interface ADRSideEffect {
  effect: string;
  probability: number;
  category: string;
}

export interface ADRResponse {
  drug: string;
  threshold: number;
  targets: string[];
  pathways: string[];
  side_effects: ADRSideEffect[];
  ai_explanation: AIExplanation;
}

export interface SearchResponse {
  matches: string[];
}
