import { useState, useEffect } from "react";

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const PI_API_KEY = "REMPLACE_PAR_TA_CLE_API"; // ← Mets ta clé API Pi ici
const SANDBOX = true; // false quand tu passes en Mainnet

// ─── MOCK DATA ────────────────────────────────────────────────────────────────
const EBOOKS = [
  {
    id: 1, title: "L'Art de la Discipline", author: "Marcus Aurelius", price: 3.14,
    category: "Développement personnel", pages: 220, rating: 4.9, sales: 1240,
    cover: "📗", color: "#1a472a",
    description: "Un guide intemporel pour maîtriser son esprit et vivre avec intention. Basé sur la philosophie stoïcienne.",
    preview: "La vraie richesse n'est pas dans ce que tu possèdes, mais dans ce que tu es capable de maîtriser...",
  },
  {
    id: 2, title: "Crypto & Blockchain Expliqués", author: "Satoshi K.", price: 5.00,
    category: "Finance & Tech", pages: 310, rating: 4.7, sales: 890,
    cover: "📘", color: "#0d2137",
    description: "Comprendre la révolution blockchain de A à Z. Parfait pour les débutants et les curieux.",
    preview: "La monnaie décentralisée n'est pas une mode, c'est un changement de paradigme fondamental...",
  },
  {
    id: 3, title: "Cuisiner avec Passion", author: "Chef Amara", price: 2.50,
    category: "Cuisine", pages: 180, rating: 4.8, sales: 2100,
    cover: "📙", color: "#5c2a00",
    description: "150 recettes africaines et méditerranéennes pour épater vos invités avec des saveurs authentiques.",
    preview: "La cuisine est un langage universel. Chaque épice raconte une histoire, chaque plat est un voyage...",
  },
  {
    id: 4, title: "Python pour les Débutants", author: "Dev Lamine", price: 4.50,
    category: "Informatique", pages: 400, rating: 4.6, sales: 670,
    cover: "📒", color: "#1a1a2e",
    description: "Apprenez Python de zéro avec des exercices pratiques et des projets réels.",
    preview: "print('Bonjour le monde !') — Ces 3 mots peuvent changer votre vie professionnelle...",
  },
  {
    id: 5, title: "Le Business Digital", author: "Fatou Diallo", price: 6.28,
    category: "Business", pages: 260, rating: 4.5, sales: 450,
    cover: "📕", color: "#3d0000",
    description: "Créer et scaler un business en ligne depuis l'Afrique. Cas réels, stratégies concrètes.",
    preview: "Le monde digital n'a pas de frontières. Votre bureau, c'est partout où vous avez du WiFi...",
  },
  {
    id: 6, title: "Méditation & Pleine Conscience", author: "Yusuf Al-Amin", price: 1.57,
    category: "Bien-être", pages: 150, rating: 4.9, sales: 3200,
    cover: "📓", color: "#1a0a2e",
    description: "Techniques de méditation adaptées à la vie moderne. 10 minutes par jour suffisent.",
    preview: "Respire. Observe. Accepte. Ces trois mots simples peuvent transformer votre relation avec le stress...",
  },
];

const CATEGORIES = ["Tous", "Développement personnel", "Finance & Tech", "Cuisine", "Informatique", "Business", "Bien-être"];

// ─── PI NETWORK SDK (RÉEL) ────────────────────────────────────────────────────
const PiSDK = {
  async init() {
    if (typeof window.Pi !== "undefined") {
      window.Pi.init({ version: "2.0", sandbox: SANDBOX });
      return true;
    }
    console.warn("Pi SDK non disponible — mode démo activé");
    await new Promise(r => setTimeout(r, 800));
    return false;
  },

  async authenticate() {
    const onIncompletePaymentFound = (payment) => {
      console.log("Paiement incomplet trouvé:", payment);
      // Gérer les paiements incomplets ici
    };

    if (typeof window.Pi !== "undefined") {
      const authResult = await window.Pi.authenticate(
        ["payments", "username"],
        onIncompletePaymentFound
      );
      return {
        uid: authResult.user.uid,
        username: authResult.user.username,
        accessToken: authResult.accessToken,
      };
    }
    // Mode démo
    await new Promise(r => setTimeout(r, 1200));
    return {
      uid: "demo_" + Math.random().toString(36).substr(2, 8),
      username: "DemoReader_" + Math.floor(Math.random() * 9999),
      accessToken: "demo_token",
    };
  },

  async createPayment(amount, memo, metadata, onApproval, onCompletion) {
    if (typeof window.Pi !== "undefined") {
      return window.Pi.createPayment(
        { amount, memo, metadata },
        {
          onReadyForServerApproval: (paymentId) => {
            fetch("/api/payments/approve", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ paymentId }),
            });
            onApproval(paymentId);
          },
          onReadyForServerCompletion: (paymentId, txid) => {
            fetch("/api/payments/complete", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ paymentId, txid, ebookId: metadata.ebookId }),
            });
            onCompletion(paymentId, txid);
          },
          onCancel: (paymentId) => console.log("Paiement annulé:", paymentId),
          onError: (error, payment) => console.error("Erreur paiement:", error, payment),
        }
      );
    }
    // Mode démo
    await new Promise(r => setTimeout(r, 800));
    const paymentId = "demo_pay_" + Date.now();
    onApproval(paymentId);
    await new Promise(r => setTimeout(r, 1500));
    onCompletion(paymentId, "demo_tx_" + Math.random().toString(36).substr(2, 16));
  }
};

// ─── COMPOSANTS UI ────────────────────────────────────────────────────────────
function StarRating({ rating }) {
  return (
    <span style={{ color: "#f4c430", fontSize: "0.75rem" }}>
      {"★".repeat(Math.floor(rating))}{"☆".repeat(5 - Math.floor(rating))}
      <span style={{ color: "#aaa", marginLeft: 4, fontSize: "0.7rem" }}>{rating}</span>
    </span>
  );
}

function PiLogo() {
  return (
    <svg width="20" height="20" viewBox="0 0 100 100" style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }}>
      <circle cx="50" cy="50" r="48" fill="#6c3fc5" />
      <text x="50" y="68" textAnchor="middle" fontSize="56" fill="white" fontFamily="serif">π</text>
    </svg>
  );
}

function Toast({ msg, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); }, []);
  const bg = type === "success" ? "#1a472a" : type === "error" ? "#5c0000" : "#1a1a3e";
  return (
    <div style={{
      position: "fixed", bottom: 24, right: 16, left: 16, zIndex: 9999, maxWidth: 400,
      margin: "0 auto", background: bg, color: "white", padding: "14px 20px",
      borderRadius: 12, boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
      animation: "slideIn 0.3s ease",
      borderLeft: `4px solid ${type === "success" ? "#4ade80" : type === "error" ? "#f87171" : "#a78bfa"}`,
      fontSize: "0.9rem", lineHeight: 1.5,
    }}>
      {type === "success" ? "✅ " : type === "error" ? "❌ " : "ℹ️ "}{msg}
    </div>
  );
}

function PaymentModal({ ebook, onClose, onSuccess, user }) {
  const [step, setStep] = useState("confirm");

  const handlePay = async () => {
    setStep("approving");
    try {
      await PiSDK.createPayment(
        ebook.price,
        `Achat: ${ebook.title}`,
        { ebookId: ebook.id, userId: user.uid },
        () => setStep("completing"),
        (paymentId, txid) => {
          setStep("done");
          setTimeout(() => { onSuccess(ebook); onClose(); }, 1800);
        }
      );
    } catch (e) {
      setStep("confirm");
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", zIndex: 1000,
      display: "flex", alignItems: "center", justifyContent: "center", padding: 20,
    }} onClick={(e) => e.target === e.currentTarget && step === "confirm" && onClose()}>
      <div style={{
        background: "#0f0f1a", borderRadius: 20, padding: 28, width: "100%", maxWidth: 360,
        border: "1px solid #2a1f5e", boxShadow: "0 24px 80px rgba(108,63,197,0.3)",
      }}>
        {step === "confirm" && (
          <>
            <div style={{ textAlign: "center", marginBottom: 20 }}>
              <div style={{ fontSize: "3rem", marginBottom: 8 }}>{ebook.cover}</div>
              <h3 style={{ color: "white", margin: "0 0 4px" }}>{ebook.title}</h3>
              <p style={{ color: "#aaa", margin: 0, fontSize: "0.85rem" }}>par {ebook.author}</p>
            </div>
            <div style={{
              background: "#1a1a2e", borderRadius: 12, padding: 16, marginBottom: 20,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{ color: "#aaa" }}>Prix total</span>
              <span style={{ color: "#a78bfa", fontSize: "1.5rem", fontWeight: 700 }}>π {ebook.price.toFixed(2)}</span>
            </div>
            <p style={{ color: "#666", fontSize: "0.78rem", textAlign: "center", marginBottom: 20 }}>
              Connecté en tant que <strong style={{ color: "#a78bfa" }}>@{user.username}</strong>
            </p>
            <button onClick={handlePay} style={{
              width: "100%", padding: 16, borderRadius: 12, border: "none",
              background: "linear-gradient(135deg, #6c3fc5, #9333ea)", color: "white",
              fontSize: "1rem", fontWeight: 700, cursor: "pointer",
            }}>
              <PiLogo /> Payer avec Pi
            </button>
            <button onClick={onClose} style={{
              width: "100%", padding: 12, borderRadius: 12, border: "1px solid #333",
              background: "transparent", color: "#666", marginTop: 10, cursor: "pointer",
            }}>Annuler</button>
          </>
        )}
        {(step === "approving" || step === "completing") && (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <div style={{ fontSize: "2.5rem", marginBottom: 16, display: "inline-block", animation: "spin 1s linear infinite" }}>⟳</div>
            <h3 style={{ color: "white", marginBottom: 8 }}>
              {step === "approving" ? "Approbation..." : "Transaction en cours..."}
            </h3>
            <p style={{ color: "#666", fontSize: "0.85rem" }}>
              {step === "approving" ? "Vérification serveur Pi..." : "Enregistrement sur la blockchain..."}
            </p>
          </div>
        )}
        {step === "done" && (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <div style={{ fontSize: "3rem", marginBottom: 12 }}>🎉</div>
            <h3 style={{ color: "#4ade80" }}>Achat réussi !</h3>
            <p style={{ color: "#aaa", fontSize: "0.85rem" }}>"{ebook.title}" ajouté à votre bibliothèque</p>
          </div>
        )}
      </div>
    </div>
  );
}

function BookCard({ ebook, owned, onBuy, onRead, onPreview }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: hover ? "#141428" : "#0d0d1f",
        borderRadius: 16, overflow: "hidden",
        border: `1px solid ${hover ? "#6c3fc5" : "#1e1e3a"}`,
        transition: "all 0.25s ease",
        transform: hover ? "translateY(-4px)" : "none",
        boxShadow: hover ? "0 12px 40px rgba(108,63,197,0.2)" : "none",
      }}
    >
      <div style={{
        height: 130, background: `linear-gradient(135deg, ${ebook.color}, #0d0d1f)`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "3.5rem", position: "relative",
      }}>
        {ebook.cover}
        {owned && (
          <div style={{
            position: "absolute", top: 8, right: 8, background: "#4ade80",
            borderRadius: 20, padding: "3px 10px", fontSize: "0.62rem", color: "#000", fontWeight: 700,
          }}>✓ Acheté</div>
        )}
        <div style={{
          position: "absolute", bottom: 8, left: 10, background: "rgba(0,0,0,0.6)",
          borderRadius: 20, padding: "3px 10px", fontSize: "0.68rem", color: "#aaa",
        }}>{ebook.pages}p</div>
      </div>
      <div style={{ padding: "12px 14px" }}>
        <div style={{ fontSize: "0.62rem", color: "#a78bfa", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
          {ebook.category}
        </div>
        <h3 style={{ color: "white", margin: "0 0 4px", fontSize: "0.9rem", fontWeight: 700, lineHeight: 1.3 }}>{ebook.title}</h3>
        <p style={{ color: "#777", margin: "0 0 6px", fontSize: "0.75rem" }}>par {ebook.author}</p>
        <StarRating rating={ebook.rating} />
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 10 }}>
          <span style={{ color: "#a78bfa", fontWeight: 700, fontSize: "1rem", flex: 1 }}>π {ebook.price.toFixed(2)}</span>
          {owned ? (
            <button onClick={() => onRead(ebook)} style={{
              padding: "7px 14px", borderRadius: 8, border: "none",
              background: "#4ade80", color: "#000", fontSize: "0.75rem", fontWeight: 700, cursor: "pointer",
            }}>📖 Lire</button>
          ) : (
            <>
              <button onClick={() => onPreview(ebook)} style={{
                padding: "7px 10px", borderRadius: 8, border: "1px solid #333",
                background: "transparent", color: "#aaa", fontSize: "0.72rem", cursor: "pointer",
              }}>Aperçu</button>
              <button onClick={() => onBuy(ebook)} style={{
                padding: "7px 12px", borderRadius: 8, border: "none",
                background: "linear-gradient(135deg, #6c3fc5, #9333ea)",
                color: "white", fontSize: "0.72rem", fontWeight: 700, cursor: "pointer",
              }}>Acheter</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function PreviewModal({ ebook, onClose, onBuy, owned }) {
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 999,
      display: "flex", alignItems: "flex-end", justifyContent: "center",
    }} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{
        background: "#0f0f1a", borderRadius: "20px 20px 0 0", padding: 24,
        width: "100%", maxWidth: 500, border: "1px solid #2a1f5e",
        maxHeight: "85vh", overflowY: "auto",
      }}>
        <div style={{ width: 40, height: 4, background: "#333", borderRadius: 2, margin: "0 auto 20px" }} />
        <div style={{ display: "flex", gap: 14, marginBottom: 16 }}>
          <div style={{
            width: 70, height: 90, borderRadius: 8, flexShrink: 0,
            background: `linear-gradient(135deg, ${ebook.color}, #0d0d1f)`,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2rem",
          }}>{ebook.cover}</div>
          <div>
            <div style={{ fontSize: "0.65rem", color: "#a78bfa", textTransform: "uppercase", letterSpacing: 1 }}>{ebook.category}</div>
            <h2 style={{ color: "white", margin: "4px 0", fontSize: "1rem" }}>{ebook.title}</h2>
            <p style={{ color: "#777", margin: "0 0 6px", fontSize: "0.8rem" }}>par {ebook.author}</p>
            <StarRating rating={ebook.rating} />
            <div style={{ color: "#a78bfa", fontWeight: 700, fontSize: "1.1rem", marginTop: 6 }}>π {ebook.price.toFixed(2)}</div>
          </div>
        </div>
        <p style={{ color: "#ccc", fontSize: "0.87rem", lineHeight: 1.7, marginBottom: 16 }}>{ebook.description}</p>
        <div style={{ background: "#1a1a2e", borderRadius: 10, padding: 14, marginBottom: 20, borderLeft: "3px solid #6c3fc5" }}>
          <p style={{ color: "#888", fontSize: "0.7rem", margin: "0 0 6px", textTransform: "uppercase" }}>Extrait</p>
          <p style={{ color: "#ccc", fontSize: "0.86rem", lineHeight: 1.7, margin: 0, fontStyle: "italic" }}>"{ebook.preview}"</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={onClose} style={{
            flex: 1, padding: 12, borderRadius: 10, border: "1px solid #333",
            background: "transparent", color: "#777", cursor: "pointer",
          }}>Fermer</button>
          {!owned && (
            <button onClick={() => { onClose(); onBuy(ebook); }} style={{
              flex: 2, padding: 12, borderRadius: 10, border: "none",
              background: "linear-gradient(135deg, #6c3fc5, #9333ea)", color: "white",
              fontWeight: 700, cursor: "pointer",
            }}><PiLogo /> Acheter π {ebook.price.toFixed(2)}</button>
          )}
        </div>
      </div>
    </div>
  );
}

function ReaderModal({ ebook, onClose }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "#0a0a12", zIndex: 1000, display: "flex", flexDirection: "column" }}>
      <div style={{
        padding: "14px 20px", background: "#0f0f1a", borderBottom: "1px solid #1e1e3a",
        display: "flex", alignItems: "center", gap: 12,
      }}>
        <button onClick={onClose} style={{ background: "none", border: "none", color: "#a78bfa", cursor: "pointer", fontSize: "1.1rem" }}>←</button>
        <div>
          <div style={{ color: "white", fontWeight: 700, fontSize: "0.9rem" }}>{ebook.title}</div>
          <div style={{ color: "#555", fontSize: "0.72rem" }}>par {ebook.author}</div>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "28px 24px", maxWidth: 680, margin: "0 auto", width: "100%" }}>
        <h1 style={{ color: "white", marginBottom: 6, fontSize: "1.6rem" }}>{ebook.title}</h1>
        <p style={{ color: "#a78bfa", marginBottom: 28 }}>par {ebook.author}</p>
        <h2 style={{ color: "#ddd", fontSize: "1rem", marginBottom: 14 }}>Chapitre 1 — Introduction</h2>
        <p style={{ color: "#ccc", lineHeight: 2, marginBottom: 20 }}>{ebook.preview}</p>
        <p style={{ color: "#ccc", lineHeight: 2, marginBottom: 20 }}>{ebook.description} Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis.</p>
        <div style={{ padding: 20, background: "#1a1a2e", borderRadius: 12, borderLeft: "3px solid #6c3fc5", color: "#888", fontStyle: "italic" }}>
          📄 Aperçu de démonstration. La version complète contient {ebook.pages} pages.
        </div>
      </div>
    </div>
  );
}

// ─── APP PRINCIPALE ───────────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState("splash");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("Tous");
  const [sort, setSort] = useState("popular");
  const [paymentEbook, setPaymentEbook] = useState(null);
  const [previewEbook, setPreviewEbook] = useState(null);
  const [readerEbook, setReaderEbook] = useState(null);
  const [library, setLibrary] = useState([]);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = "info") => setToast({ msg, type });

  useEffect(() => {
    PiSDK.init().then(() => setScreen("home"));
  }, []);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const u = await PiSDK.authenticate();
      setUser(u);
      showToast(`Bienvenue, @${u.username} !`, "success");
    } catch {
      showToast("Erreur de connexion Pi.", "error");
    }
    setLoading(false);
  };

  const handleBuy = (ebook) => {
    if (!user) { showToast("Connectez-vous avec Pi pour acheter.", "info"); return; }
    if (library.find(e => e.id === ebook.id)) { showToast("Vous possédez déjà ce livre.", "info"); return; }
    setPaymentEbook(ebook);
  };

  const handlePurchaseSuccess = (ebook) => {
    setLibrary(prev => [...prev, { ...ebook, purchasedAt: new Date().toISOString() }]);
    showToast(`"${ebook.title}" ajouté à votre bibliothèque !`, "success");
  };

  const filtered = EBOOKS
    .filter(e => category === "Tous" || e.category === category)
    .filter(e => e.title.toLowerCase().includes(search.toLowerCase()) || e.author.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => sort === "popular" ? b.sales - a.sales : sort === "price_asc" ? a.price - b.price : sort === "price_desc" ? b.price - a.price : b.rating - a.rating);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=Space+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Sora', sans-serif; background: #07070f; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #3a2a6e; border-radius: 3px; }
        @keyframes fadeIn { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
        @keyframes spin { from { transform:rotate(0deg); } to { transform:rotate(360deg); } }
        @keyframes slideIn { from { transform:translateY(100%); opacity:0; } to { transform:none; opacity:1; } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        button { font-family: 'Sora', sans-serif; transition: opacity 0.15s; }
        button:hover { opacity: 0.88; }
        input, select { font-family: 'Sora', sans-serif; }
      `}</style>

      <div style={{ minHeight: "100vh", background: "#07070f" }}>

        {/* SPLASH */}
        {screen === "splash" && (
          <div style={{
            minHeight: "100vh", display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center", gap: 16,
          }}>
            <div style={{ fontSize: "3rem", animation: "pulse 1.5s ease infinite" }}>📚</div>
            <p style={{ color: "#6c3fc5", fontFamily: "'Space Mono', monospace", fontSize: "0.85rem" }}>
              Chargement Pi SDK...
            </p>
          </div>
        )}

        {/* HEADER */}
        {screen !== "splash" && !readerEbook && (
          <header style={{
            background: "rgba(7,7,15,0.96)", backdropFilter: "blur(12px)",
            borderBottom: "1px solid #1e1e3a", padding: "0 20px",
            position: "sticky", top: 0, zIndex: 100,
            display: "flex", alignItems: "center", gap: 12, height: 60,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
              <PiLogo />
              <span style={{ color: "white", fontWeight: 800, fontSize: "1rem", fontFamily: "'Space Mono', monospace" }}>
                eBook<span style={{ color: "#a78bfa" }}>Store</span>
              </span>
            </div>
            <button onClick={() => setScreen("home")} style={{
              padding: "6px 12px", borderRadius: 8, border: "none", cursor: "pointer",
              background: screen === "home" ? "#6c3fc5" : "transparent",
              color: screen === "home" ? "white" : "#777", fontSize: "0.78rem", fontWeight: 600,
            }}>Catalogue</button>
            <button onClick={() => setScreen("library")} style={{
              padding: "6px 12px", borderRadius: 8, border: "none", cursor: "pointer",
              background: screen === "library" ? "#6c3fc5" : "transparent",
              color: screen === "library" ? "white" : "#777", fontSize: "0.78rem", fontWeight: 600,
            }}>📚 {library.length > 0 && `(${library.length})`}</button>
            {user ? (
              <div style={{
                background: "#1a1a2e", borderRadius: 16, padding: "5px 12px",
                display: "flex", alignItems: "center", gap: 6,
              }}>
                <div style={{ width: 6, height: 6, background: "#4ade80", borderRadius: "50%" }} />
                <span style={{ color: "#a78bfa", fontSize: "0.72rem", fontFamily: "'Space Mono', monospace" }}>
                  @{user.username.substring(0, 10)}
                </span>
              </div>
            ) : (
              <button onClick={handleLogin} disabled={loading} style={{
                padding: "8px 14px", borderRadius: 8, border: "none",
                background: loading ? "#2a1f5e" : "linear-gradient(135deg, #6c3fc5, #9333ea)",
                color: "white", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer",
              }}>
                {loading ? "..." : <><PiLogo />Connexion</>}
              </button>
            )}
          </header>
        )}

        {/* CATALOGUE */}
        {screen === "home" && (
          <div style={{ padding: "24px 16px", maxWidth: 800, margin: "0 auto", animation: "fadeIn 0.4s ease" }}>
            {/* Hero */}
            <div style={{
              background: "linear-gradient(135deg, #1a0a3e, #0d0d2a)",
              borderRadius: 18, padding: "28px 24px", marginBottom: 24,
              border: "1px solid #2a1f5e", position: "relative", overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", top: -30, right: -30, width: 150, height: 150,
                background: "radial-gradient(circle, rgba(108,63,197,0.35) 0%, transparent 70%)",
                borderRadius: "50%",
              }} />
              <div style={{ fontSize: "0.68rem", color: "#a78bfa", textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 }}>
                🌍 Librairie numérique sur Pi Network
              </div>
              <h1 style={{ color: "white", fontSize: "1.6rem", fontWeight: 800, marginBottom: 10, lineHeight: 1.2 }}>
                Ebooks payables<br /><span style={{ color: "#a78bfa" }}>en Pi Coin</span>
              </h1>
              <div style={{ display: "flex", gap: 20, marginTop: 16 }}>
                {[["📚", `${EBOOKS.length}+`, "Ebooks"], ["⭐", "4.7", "Note moy."], ["👥", "8K+", "Lecteurs"]].map(([ic, v, l]) => (
                  <div key={l}>
                    <div style={{ color: "white", fontWeight: 700, fontSize: "1.1rem" }}>{ic} {v}</div>
                    <div style={{ color: "#555", fontSize: "0.68rem" }}>{l}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Search */}
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="🔍 Rechercher..."
              style={{
                width: "100%", padding: "12px 16px", borderRadius: 10, marginBottom: 14,
                background: "#0d0d1f", border: "1px solid #1e1e3a", color: "white",
                fontSize: "0.88rem", outline: "none",
              }}
            />

            {/* Categories */}
            <div style={{ display: "flex", gap: 8, marginBottom: 16, overflowX: "auto", paddingBottom: 4 }}>
              {CATEGORIES.map(cat => (
                <button key={cat} onClick={() => setCategory(cat)} style={{
                  padding: "6px 14px", borderRadius: 20, border: "none", cursor: "pointer",
                  background: category === cat ? "#6c3fc5" : "#1a1a2e",
                  color: category === cat ? "white" : "#777",
                  fontSize: "0.75rem", fontWeight: 600, whiteSpace: "nowrap",
                }}>{cat}</button>
              ))}
            </div>

            {/* Sort */}
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
              <select value={sort} onChange={e => setSort(e.target.value)} style={{
                padding: "8px 12px", borderRadius: 8, background: "#0d0d1f",
                border: "1px solid #1e1e3a", color: "#aaa", outline: "none", fontSize: "0.8rem",
              }}>
                <option value="popular">Plus populaires</option>
                <option value="rating">Mieux notés</option>
                <option value="price_asc">Prix croissant</option>
                <option value="price_desc">Prix décroissant</option>
              </select>
            </div>

            {/* Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 14 }}>
              {filtered.map(ebook => (
                <BookCard
                  key={ebook.id} ebook={ebook}
                  owned={!!library.find(e => e.id === ebook.id)}
                  onBuy={handleBuy} onRead={setReaderEbook} onPreview={setPreviewEbook}
                />
              ))}
            </div>
            {filtered.length === 0 && (
              <div style={{ textAlign: "center", padding: 60, color: "#555" }}>
                <div style={{ fontSize: "2.5rem", marginBottom: 10 }}>📭</div>
                Aucun résultat trouvé
              </div>
            )}
          </div>
        )}

        {/* LIBRARY */}
        {screen === "library" && (
          <div style={{ padding: "24px 16px", maxWidth: 800, margin: "0 auto", animation: "fadeIn 0.4s ease" }}>
            <h2 style={{ color: "white", marginBottom: 6 }}>Ma Bibliothèque</h2>
            <p style={{ color: "#555", marginBottom: 24, fontSize: "0.85rem" }}>
              {library.length} livre{library.length !== 1 ? "s" : ""} acheté{library.length !== 1 ? "s" : ""}
            </p>
            {library.length === 0 ? (
              <div style={{ textAlign: "center", padding: 60, color: "#555" }}>
                <div style={{ fontSize: "3.5rem", marginBottom: 14 }}>📚</div>
                <h3 style={{ color: "#888", marginBottom: 8, fontSize: "1rem" }}>Bibliothèque vide</h3>
                <p style={{ marginBottom: 20, fontSize: "0.85rem" }}>Achetez votre premier ebook pour commencer</p>
                <button onClick={() => setScreen("home")} style={{
                  padding: "12px 24px", borderRadius: 10, border: "none",
                  background: "linear-gradient(135deg, #6c3fc5, #9333ea)",
                  color: "white", fontWeight: 700, cursor: "pointer",
                }}>Voir le catalogue</button>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 14 }}>
                {library.map(ebook => (
                  <BookCard key={ebook.id} ebook={ebook} owned={true}
                    onBuy={handleBuy} onRead={setReaderEbook} onPreview={setPreviewEbook} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* FOOTER */}
        {screen !== "splash" && !readerEbook && (
          <footer style={{
            borderTop: "1px solid #1e1e3a", padding: "16px 20px",
            textAlign: "center", color: "#333", fontSize: "0.72rem", marginTop: 40,
          }}>
            <PiLogo /> Pi eBook Store — Construit sur Pi Network
          </footer>
        )}
      </div>

      {/* MODALS */}
      {paymentEbook && (
        <PaymentModal ebook={paymentEbook} user={user}
          onClose={() => setPaymentEbook(null)} onSuccess={handlePurchaseSuccess} />
      )}
      {previewEbook && (
        <PreviewModal ebook={previewEbook} onClose={() => setPreviewEbook(null)}
          onBuy={handleBuy} owned={!!library.find(e => e.id === previewEbook.id)} />
      )}
      {readerEbook && <ReaderModal ebook={readerEbook} onClose={() => setReaderEbook(null)} />}
      {toast && <Toast msg={toast.msg} type={toast.type} onClose={() => setToast(null)} />}
    </>
  );
}
