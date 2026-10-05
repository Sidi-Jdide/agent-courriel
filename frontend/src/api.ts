import type { Courriel, FiltresCourriels, PageCourriels, Sante, Statistiques } from './types'

export class ErreurApi extends Error {
  constructor(public statut: number, message: string) {
    super(message)
  }
}

async function requete<T>(chemin: string, options: RequestInit = {}): Promise<T> {
  let reponse: Response
  try {
    reponse = await fetch(`/api${chemin}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch {
    throw new ErreurApi(0, 'Serveur injoignable. Le backend FastAPI est-il démarré ?')
  }
  if (!reponse.ok) {
    let message = `Erreur ${reponse.status}`
    try {
      const corps = await reponse.json()
      if (typeof corps.detail === 'string') message = corps.detail
    } catch {
      /* corps non JSON */
    }
    throw new ErreurApi(reponse.status, message)
  }
  return reponse.json() as Promise<T>
}

function enParametres(filtres: FiltresCourriels): string {
  const p = new URLSearchParams()
  for (const [cle, valeur] of Object.entries(filtres)) {
    if (valeur !== undefined && valeur !== '' && valeur !== null) p.set(cle, String(valeur))
  }
  const texte = p.toString()
  return texte ? `?${texte}` : ''
}

export const api = {
  sante: () => requete<Sante>('/sante'),
  statistiques: () => requete<Statistiques>('/statistiques'),
  courriels: (filtres: FiltresCourriels = {}) => requete<PageCourriels>(`/courriels${enParametres(filtres)}`),
  courriel: (id: string) => requete<Courriel>(`/courriels/${encodeURIComponent(id)}`),
  approuver: (id: string, texte?: string) =>
    requete<Courriel>(`/courriels/${encodeURIComponent(id)}/approuver`, {
      method: 'POST',
      body: JSON.stringify({ texte }),
    }),
  rejeter: (id: string) => requete<Courriel>(`/courriels/${encodeURIComponent(id)}/rejeter`, { method: 'POST' }),
  lancerCycle: () => requete<{ bilan: Record<string, number> }>('/agent/cycle', { method: 'POST' }),
}
