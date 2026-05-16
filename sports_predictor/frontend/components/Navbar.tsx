"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, Clock, Home, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/matches", label: "Matches", icon: Activity },
  { href: "/history", label: "History", icon: Clock },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 inset-x-0 z-50 h-14 bg-dark-900/90 backdrop-blur border-b border-slate-700/50">
      <div className="max-w-7xl mx-auto h-full px-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-slate-100">
          <Zap className="w-5 h-5 text-brand-400" />
          <span>SportPredictor</span>
          <span className="text-brand-400">Pro</span>
        </Link>

        <nav className="flex items-center gap-1">
          {nav.map(({ href, label, icon: Icon }) => (
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

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Live</span>
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
          </div>
        </div>
      </div>
    </header>
  );
}
