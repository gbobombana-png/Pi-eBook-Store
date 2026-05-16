"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Key, Wifi, WifiOff, Database, Brain, RefreshCw,
  CheckCircle, XCircle, Clock, AlertTriangle, Shield
} from "lucide-react";
import { getUser, authHeaders } from "@/lib/auth";
import { cn } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

async function adminFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${API}/api/v1/admin${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(options?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail ?? `Erreur ${res.status}`);
  }
  return res.json();
}

interface ApiStatus { status: string; plan?: string; requests_remaining?: string; requests_limit?: string; remaining?: string; used?: string; detail?: string; }
interface CollectStatus { matches_total: number; matches_finished: number; teams_total: number; ml_ready: boolean; }
interface ModelStats { model_exists: boolean; model_size?: string; model_last_trained?: string; n_features?: number; training_samples_available: number; mode: string; }

export default function AdminPage() {
  const router = useRouter();
  const user = getUser();

  const [apiFootballKey, setApiFootballKey] = useState("");
  const [oddsApiKey, setOddsApiKey] = useState("");
  const [savingKeys, setSavingKeys] = useState(false);
  const [keysSaved, setKeysSaved] = useState(false);

  const [testResult, setTestResult] = useState<{ api_football: ApiStatus; odds_api: ApiStatus } | null>(null);
  const [testing, setTesting] = useState(false);

  const [collectStatus, setCollectStatus] = useState<CollectStatus | null>(null);
  const [collecting, setCollecting] = useState(false);

  const [modelStats, setModelStats] = useState<ModelStats | null>(null);
  const [training, setTraining] = useState(false);

  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.is_admin) { router.push("/login"); return; }
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [cs, ms] = await Promise.all([
        adminFetch("/collect/status"),
        adminFetch("/model/stats"),
      ]);
      setCollectStatus(cs);
      setModelStats(ms);
    } catch (e) {
      notify("Erreur de chargement", false);
    } finally {
      setLoading(false);
    }
  };

  const notify = (text: string, ok: boolean) => {
    setMessage({ text, ok });
    setTimeout(() => setMessage(null), 4000);
  };

  const handleSaveKeys = async () => {
    setSavingKeys(true);
    try {
      await adminFetch("/api-keys", {
        method: "POST",
        body: JSON.stringify({ api_football_key: apiFootballKey, odds_api_key: oddsApiKey }),
      });
      setKeysSaved(true);
      notify("Clés sauvegardées ✓", true);
    } catch (e: any) {
      notify(e.message, false);
    } finally {
      setSavingKeys(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await adminFetch("/api-keys/test");
      setTestResult(r);
    } catch (e: any) {
      notify(e.message, false);
    } finally {
      setTesting(false);
    }
  };

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await adminFetch("/collect", { method: "POST" });
      notify("Collecte démarrée en arrière-plan — revenez dans quelques minutes", true);
      setTimeout(loadAll, 10000);
    } catch (e: any) {
      notify(e.message, false);
    } finally {
      setCollecting(false);
    }
  };

  const handleTrain = async (synthetic = false) => {
    setTraining(true);
    try {
      await adminFetch(`/train?force_synthetic=${synthetic}`, { method: "POST" });
      notify("Entraînement démarré en arrière-plan", true);
      setTimeout(loadAll, 15000);
    } catch (e: any) {
      notify(e.message, false);
    } finally {
      setTraining(false);
    }
  };

  const StatusIcon = ({ s }: { s: string }) =>
    s === "ok" ? <CheckCircle className="w-4 h-4 text-brand-400" /> :
    s === "not_configured" ? <Clock className="w-4 h-4 text-amber-400" /> :
    <XCircle className="w-4 h-4 text-rose-400" />;

  if (!user?.is_admin) return null;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2 mb-8">
        <Shield className="w-6 h-6 text-brand-400" />
        Administration
      </h1>

      {message && (
        <div className={cn("card mb-6 flex items-center gap-2 text-sm border",
          message.ok ? "border-brand-500/30 bg-brand-500/5 text-brand-300" : "border-rose-500/30 bg-rose-500/5 text-rose-300")}>
          {message.ok ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
          {message.text}
        </div>
      )}

      {/* ── Clés API ── */}
      <section className="card mb-6">
        <h2 className="font-semibold text-slate-100 flex items-center gap-2 mb-4">
          <Key className="w-4 h-4 text-brand-400" /> Clés API
        </h2>
        <div className="space-y-3 mb-4">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">API-Football (RapidAPI)</label>
            <input type="password" value={apiFootballKey} onChange={e => setApiFootballKey(e.target.value)}
              placeholder="Coller votre clé ici"
              className="w-full bg-dark-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-brand-500" />
            <p className="text-xs text-slate-600 mt-1">Obtenir sur rapidapi.com → API-Football</p>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">TheOddsAPI</label>
            <input type="password" value={oddsApiKey} onChange={e => setOddsApiKey(e.target.value)}
              placeholder="Coller votre clé ici"
              className="w-full bg-dark-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-brand-500" />
            <p className="text-xs text-slate-600 mt-1">Obtenir sur the-odds-api.com</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={handleSaveKeys} disabled={savingKeys || (!apiFootballKey && !oddsApiKey)} className="btn-primary flex items-center gap-1.5">
            {savingKeys ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Key className="w-3.5 h-3.5" />}
            Sauvegarder
          </button>
          <button onClick={handleTest} disabled={testing} className="btn-ghost flex items-center gap-1.5">
            {testing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Wifi className="w-3.5 h-3.5" />}
            Tester les connexions
          </button>
        </div>

        {testResult && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            {[
              { label: "API-Football", data: testResult.api_football },
              { label: "TheOddsAPI", data: testResult.odds_api },
            ].map(({ label, data }) => (
              <div key={label} className="card-sm">
                <div className="flex items-center gap-2 mb-2">
                  <StatusIcon s={data.status} />
                  <span className="text-sm font-medium text-slate-200">{label}</span>
                </div>
                {data.status === "ok" ? (
                  <div className="text-xs text-slate-500 space-y-0.5">
                    {data.plan && <p>Plan : <span className="text-slate-300">{data.plan}</span></p>}
                    {data.requests_remaining && <p>Restants : <span className="text-slate-300">{data.requests_remaining}/{data.requests_limit}</span></p>}
                    {data.remaining && <p>Restants : <span className="text-slate-300">{data.remaining}</span></p>}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">{data.detail || data.status}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Collecte ── */}
      <section className="card mb-6">
        <h2 className="font-semibold text-slate-100 flex items-center gap-2 mb-4">
          <Database className="w-4 h-4 text-brand-400" /> Données historiques
        </h2>
        {collectStatus && (
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="card-sm text-center">
              <p className="stat-label mb-1">Matchs total</p>
              <p className="stat-value">{collectStatus.matches_total}</p>
            </div>
            <div className="card-sm text-center">
              <p className="stat-label mb-1">Terminés</p>
              <p className="stat-value">{collectStatus.matches_finished}</p>
            </div>
            <div className="card-sm text-center">
              <p className="stat-label mb-1">Équipes</p>
              <p className="stat-value">{collectStatus.teams_total}</p>
            </div>
          </div>
        )}
        <div className={cn("text-xs rounded-lg px-3 py-2 mb-4 border",
          collectStatus?.ml_ready
            ? "bg-brand-500/10 border-brand-500/30 text-brand-300"
            : "bg-amber-500/10 border-amber-500/30 text-amber-300")}>
          {collectStatus?.ml_ready
            ? `✓ Assez de données pour l'entraînement ML (${collectStatus.matches_finished} matchs)`
            : `⚠ Minimum 100 matchs terminés requis — actuellement ${collectStatus?.matches_finished ?? 0}`}
        </div>
        <button onClick={handleCollect} disabled={collecting} className="btn-primary flex items-center gap-1.5">
          {collecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Database className="w-3.5 h-3.5" />}
          {collecting ? "Collecte en cours…" : "Collecter les données (6 ligues × 2 saisons)"}
        </button>
        <p className="text-xs text-slate-600 mt-2">Nécessite une clé API-Football valide. Durée : ~5 min.</p>
      </section>

      {/* ── ML ── */}
      <section className="card">
        <h2 className="font-semibold text-slate-100 flex items-center gap-2 mb-4">
          <Brain className="w-4 h-4 text-brand-400" /> Modèle ML
        </h2>
        {modelStats && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="card-sm">
              <p className="stat-label mb-1">Mode actuel</p>
              <p className="text-sm font-semibold text-slate-200">{modelStats.mode}</p>
            </div>
            <div className="card-sm">
              <p className="stat-label mb-1">Taille modèle</p>
              <p className="text-sm font-semibold text-slate-200">{modelStats.model_size ?? "—"}</p>
            </div>
            <div className="card-sm">
              <p className="stat-label mb-1">Dernier entraînement</p>
              <p className="text-xs text-slate-300">{modelStats.model_last_trained ? new Date(modelStats.model_last_trained).toLocaleString("fr-FR") : "Jamais"}</p>
            </div>
            <div className="card-sm">
              <p className="stat-label mb-1">Features</p>
              <p className="text-sm font-semibold text-slate-200">{modelStats.n_features ?? "—"}</p>
            </div>
          </div>
        )}
        <div className="flex gap-2">
          <button onClick={() => handleTrain(false)} disabled={training} className="btn-primary flex items-center gap-1.5">
            {training ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Brain className="w-3.5 h-3.5" />}
            Entraîner (données DB)
          </button>
          <button onClick={() => handleTrain(true)} disabled={training} className="btn-ghost flex items-center gap-1.5">
            <Brain className="w-3.5 h-3.5" />
            Entraîner (synthétique)
          </button>
          <button onClick={loadAll} disabled={loading} className="btn-ghost flex items-center gap-1.5">
            <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-2">Réentraînement automatique chaque lundi à 03:00 UTC.</p>
      </section>
    </div>
  );
}
