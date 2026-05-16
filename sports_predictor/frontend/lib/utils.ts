import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function confidenceColor(confidence: number): string {
  if (confidence >= 75) return "text-green-400";
  if (confidence >= 60) return "text-yellow-400";
  return "text-red-400";
}

export function confidenceBg(confidence: number): string {
  if (confidence >= 75) return "bg-green-500/20";
  if (confidence >= 60) return "bg-yellow-500/20";
  return "bg-red-500/20";
}

export function betTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    home: "Victoire Domicile (1)",
    draw: "Match Nul (X)",
    away: "Victoire Extérieur (2)",
    btts_yes: "Les deux équipes marquent (Oui)",
    btts_no: "Les deux équipes marquent (Non)",
    over25: "Plus de 2.5 buts",
    under25: "Moins de 2.5 buts",
  };
  return labels[type] ?? type;
}

export function formatOdds(odds: number): string {
  return odds.toFixed(2);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export function pct(n: number): string {
  return `${Math.min(100, Math.max(0, n)).toFixed(0)}%`;
}
