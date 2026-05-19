// Middleware — vérifie l'identité Pi Network via l'access token du SDK

const PI_API_BASE = process.env.PI_API_BASE || 'https://api.minepi.com/v2';

export async function piAuthMiddleware(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Token Pi manquant' });
  }

  const accessToken = authHeader.slice(7);

  try {
    const response = await fetch(`${PI_API_BASE}/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (!response.ok) {
      return res.status(401).json({ error: 'Token Pi invalide ou expiré' });
    }

    const piUser = await response.json();
    req.piUser = piUser; // { uid, username, ... }
    next();
  } catch (err) {
    console.error('[piAuth] Erreur vérification token:', err.message);
    res.status(502).json({ error: 'Impossible de contacter Pi Network' });
  }
}

// Middleware allégé pour le mode démo (pas de vrai SDK disponible)
export function demoAuthMiddleware(req, res, next) {
  const uid = req.headers['x-demo-uid'];
  const username = req.headers['x-demo-username'] || 'DemoPlayer';
  if (!uid) return res.status(401).json({ error: 'x-demo-uid requis en mode démo' });
  req.piUser = { uid, username };
  next();
}

// Choisit automatiquement selon NODE_ENV
export function authMiddleware(req, res, next) {
  if (process.env.NODE_ENV === 'development' && req.headers['x-demo-uid']) {
    return demoAuthMiddleware(req, res, next);
  }
  return piAuthMiddleware(req, res, next);
}
