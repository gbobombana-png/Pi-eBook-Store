"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, BarChart3, Clock, Home, LogIn, LogOut, Shield, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { getUser, logout, AuthUser } from "@/lib/auth";

const publicNav = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/matches", label: "Matchs", icon: Activity },
  { href: "/history", label: "Historique", icon: Clock },
];
const adminNav = [
  { href: "/admin", label: "Admin", icon: Shield },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, [pathname]);

  const handleLogout = () => {
    logout();
    setUser(null);
    router.push("/login");
  };

  return (
    <header className="fixed top-0 inset-x-0 z-50 h-14 bg-dark-900/90 backdrop-blur border-b border-slate-700/50">
      <div className="max-w-7xl mx-auto h-full px-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-slate-100">
          <Zap className="w-5 h-5 text-brand-400" />
          <span>SportPredictor</span>
          <span className="text-brand-400">Pro</span>
        </Link>

        <nav className="flex items-center gap-1">
          {[...publicNav, ...(user?.is_admin ? adminNav : [])].map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                pathname === href
                  ? "bg-brand-500/20 text-brand-400"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Live</span>
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
          </div>

          {user ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 flex items-center gap-1">
                {user.is_admin && <Shield className="w-3 h-3 text-amber-400" />}
                {user.username}
              </span>
              <button
                onClick={handleLogout}
                className="btn-ghost flex items-center gap-1 text-xs"
              >
                <LogOut className="w-3.5 h-3.5" />
                Déconnexion
              </button>
            </div>
          ) : (
            <Link href="/login" className="btn-primary flex items-center gap-1.5 text-xs py-1.5">
              <LogIn className="w-3.5 h-3.5" />
              Connexion
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
