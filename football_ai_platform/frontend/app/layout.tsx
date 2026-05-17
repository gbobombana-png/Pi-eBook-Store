import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Football AI Platform",
  description: "Analyse footballistique IA — Prédiction & Détection de matchs suspects",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark">
      <body className="min-h-screen bg-[#030712] text-gray-100 antialiased">
        {/* Sidebar navigation */}
        <div className="flex min-h-screen">
          <aside className="fixed left-0 top-0 h-screen w-16 lg:w-56 bg-gray-950 border-r border-gray-800 flex flex-col z-50">
            {/* Logo */}
            <div className="p-4 border-b border-gray-800">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-sm font-black">
                  ⚽
                </div>
                <span className="hidden lg:block text-sm font-bold text-white">Football AI</span>
              </div>
            </div>

            {/* Nav links */}
            <nav className="flex-1 p-3 space-y-1">
              {[
                { href: "/",          icon: "📊", label: "Dashboard"   },
                { href: "/matches",   icon: "🗓",  label: "Matchs"     },
                { href: "/live",      icon: "⚡",  label: "Live"       },
                { href: "/analysis",  icon: "🔍",  label: "Analyse"    },
                { href: "/alerts",    icon: "🚨",  label: "Alertes"    },
              ].map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800 transition-all text-sm font-medium"
                >
                  <span className="text-base">{item.icon}</span>
                  <span className="hidden lg:block">{item.label}</span>
                </a>
              ))}
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-gray-800">
              <p className="hidden lg:block text-xs text-gray-600">v1.0.0 · Football AI</p>
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 ml-16 lg:ml-56 min-h-screen">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
