export interface ScoreBreakdown {
  form: number;
  psychology: number;
  squad: number;
  tactics: number;
  advanced: number;
  odds: number;
  ml: number;
  total: number;
}

export interface KeyStats {
  home_xg_avg: number;
  away_xg_avg: number;
  home_form5: string;
  away_form5: string;
  h2h_home_wins: number;
  h2h_draws: number;
  h2h_away_wins: number;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  prob_btts: number;
  prob_over25: number;
  value_edge_pct: number;
  scores: ScoreBreakdown;
}

export interface Bet {
  fixture_id: number;
  match: string;
  competition: string;
  kickoff: string;
  bet_type: string;
  odds: number;
  confidence: number;
  value_edge: number;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  prob_btts: number;
  prob_over25: number;
  reasoning: string;
  risks: string;
  key_stats: KeyStats;
  score_breakdown: ScoreBreakdown;
}

export interface Ticket {
  ticket_number: number;
  label: string;
  total_odds: number;
  stake: number;
  potential_gain: number;
  bets: Bet[];
}

export interface DailyTickets {
  date: string;
  generated_at: string;
  tickets: Ticket[];
  total_tickets: number;
}
