export const CATEGORIES: Record<string, string> = {
  question_frequente: 'Question fréquente',
  question_client: 'Question client',
  demande_rdv: 'Rendez-vous',
  plainte: 'Plainte',
  accuse_reception: 'Remerciement',
  facture_paiement: 'Facture / paiement',
  notification_auto: 'Notification',
  publicite_spam: 'Publicité',
  autre: 'Autre',
}

export const ACTIONS: Record<string, string> = {
  brouillon: 'Brouillon',
  envoyé: 'Envoyé auto',
  classé: 'Classé',
  ignoré: 'Ignoré',
}

export const STATUTS: Record<string, string> = {
  en_attente: 'À valider',
  approuvé: 'Approuvé',
  rejeté: 'Rejeté',
  envoyé: 'Envoyé auto',
}

/** Ton visuel d'un badge : attention (ambre), succes (vert), neutre (gris), danger (rouge). */
export type Ton = 'attention' | 'succes' | 'neutre' | 'danger'

export function etatCourriel(c: { action: string; statut: string | null }): { libelle: string; ton: Ton } {
  if (c.statut && c.statut !== '-') {
    const ton: Ton = c.statut === 'en_attente' ? 'attention' : c.statut === 'rejeté' ? 'neutre' : 'succes'
    return { libelle: STATUTS[c.statut] ?? c.statut, ton }
  }
  return { libelle: ACTIONS[c.action] ?? c.action, ton: c.action === 'envoyé' ? 'succes' : 'neutre' }
}

export const libelleCategorie = (c: string) => CATEGORIES[c] ?? (c === '-' ? '—' : c)

const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']

/** « il y a 5 min », « il y a 3 h », sinon « 4 oct., 14 h 05 ». */
export function formaterDate(iso: string, maintenant: Date = new Date()): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const minutes = Math.round((maintenant.getTime() - d.getTime()) / 60000)
  if (minutes >= 0 && minutes < 1) return "à l'instant"
  if (minutes >= 0 && minutes < 60) return `il y a ${minutes} min`
  if (minutes >= 0 && minutes < 12 * 60) return `il y a ${Math.round(minutes / 60)} h`
  return `${d.getDate()} ${MOIS[d.getMonth()]}, ${d.getHours()} h ${String(d.getMinutes()).padStart(2, '0')}`
}
