// Reflète les schémas Pydantic de api/schemas.py

export type Action = 'brouillon' | 'envoyé' | 'classé' | 'ignoré'
export type Statut = 'en_attente' | 'approuvé' | 'rejeté' | 'envoyé' | '-'

export interface Courriel {
  id: string
  date: string
  expediteur: string
  sujet: string
  categorie: string
  priorite: string
  action: Action
  statut: Statut | null
  resume: string | null
  raison: string | null
  reponse: string | null
  brouillon_id: string | null
}

export interface PageCourriels {
  elements: Courriel[]
  total: number
  page: number
  taille: number
}

export interface Statistiques {
  total: number
  en_attente: number
  par_action: Record<string, number>
  par_categorie: Record<string, number>
}

export interface Sante {
  statut: 'ok'
  mode: 'demo' | 'gmail'
  envoi_auto: boolean
  modele: string
}

export interface FiltresCourriels {
  action?: string
  categorie?: string
  statut?: string
  q?: string
  page?: number
  taille?: number
}
