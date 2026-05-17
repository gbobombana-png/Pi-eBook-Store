export type SuspicionLevel = "low" | "medium" | "high" | "critical";
export type MatchStatus = "scheduled" | "live" | "finished" | "cancelled";

export interface SuspicionFlag {
  code: string;
  description: string;
  severity: SuspicionLevel;
  score_contribution: number;
}

export interface ModelPrediction {
  model_name: string;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  predicted_home_score: number;
  predicted_away_score: number;
  exact_score_prob: number;
  confidence: number;
}

export interface EnsembleResult {
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  predicted_home_score: number;
  predicted_away_score: number;
  exact_score_probability: number;
  prob_over25: number;
  prob_btts: number;
  prob_ht_home_lead: number;
  prob_late_goal: number;
  model_agreement: number;
  predictions: ModelPrediction[];
}

export interface OddsAnalysisResult {
  opening_home: number | null;
  opening_away: number | null;
  current_home: number;
  current_away: number;
  movement_home_pct: number;
  movement_away_pct: number;
  is_sharp_move: boolean;
  sharp_direction: "home" | "away" | null;
  volume_anomaly: boolean;
  volume_multiplier: number;
  market_inversion: boolean;
  bookmaker_consensus_pct: number;
  suspicion_contribution: number;
}

export interface FootballStatsResult {
  home_attack_strength: number;
  away_attack_strength: number;
  home_defense_strength: number;
  away_defense_strength: number;
  expected_home_goals: number;
  expected_away_goals: number;
  h2h_home_wins: number;
  h2h_draws: number;
  h2h_away_wins: number;
  h2h_avg_goals: number;
  form_home_score: number;
  form_away_score: number;
  home_advantage_factor: number;
  suspicion_contribution: number;
}

export interface SuspicionResult {
  score: number;
  level: SuspicionLevel;
  flags: SuspicionFlag[];
  similar_suspect_matches: string[];
  risk_assessment: string;
}

export interface MatchOut {
  id: number;
  external_id: string;
  competition: string;
  home_team: string;
  away_team: string;
  match_date: string;
  status: MatchStatus;
  home_score: number | null;
  away_score: number | null;
  home_xg: number | null;
  away_xg: number | null;
  home_shots: number | null;
  away_shots: number | null;
  home_possession: number | null;
  away_possession: number | null;
  home_form: string | null;
  away_form: string | null;
}

export interface FullAnalysisResponse {
  match: MatchOut;
  odds_analysis: OddsAnalysisResult;
  football_stats: FootballStatsResult;
  prediction: EnsembleResult;
  suspicion: SuspicionResult;
  predicted_winner: string;
  prediction_confidence: number;
  analysis_timestamp: string;
  markets: Record<string, unknown>;
}

export interface DashboardMatchCard {
  match_id: number;
  home_team: string;
  away_team: string;
  match_date: string;
  competition: string;
  status: MatchStatus;
  suspicion_score: number;
  suspicion_level: SuspicionLevel;
  predicted_winner: string;
  prediction_confidence: number;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  predicted_score: string;
  key_flags: string[];
}

export interface OddsDataPoint {
  timestamp: string;
  home: number;
  draw: number;
  away: number;
  volume?: number;
}

export interface LiveUpdate {
  type: string;
  match_id?: number;
  minute?: number;
  home_score?: number;
  away_score?: number;
  event?: string;
  prob_home?: number;
  prob_draw?: number;
  prob_away?: number;
  suspicion_delta?: number;
  alert?: string;
}
