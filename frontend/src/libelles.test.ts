import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BadgeEtat from './components/BadgeEtat.vue'
import { etatCourriel, formaterDate, libelleCategorie } from './libelles'

describe('etatCourriel', () => {
  it('un brouillon en attente demande une action', () => {
    expect(etatCourriel({ action: 'brouillon', statut: 'en_attente' })).toEqual({ libelle: 'À valider', ton: 'attention' })
  })
  it('un envoi automatique est un succès', () => {
    expect(etatCourriel({ action: 'envoyé', statut: 'envoyé' }).ton).toBe('succes')
  })
  it('sans statut, on affiche l’action', () => {
    expect(etatCourriel({ action: 'ignoré', statut: '-' })).toEqual({ libelle: 'Ignoré', ton: 'neutre' })
  })
})

describe('formaterDate', () => {
  const maintenant = new Date('2026-10-05T12:00:00Z')
  it('dates récentes en relatif', () => {
    expect(formaterDate('2026-10-05T11:55:00Z', maintenant)).toBe('il y a 5 min')
    expect(formaterDate('2026-10-05T09:00:00Z', maintenant)).toBe('il y a 3 h')
  })
  it('dates anciennes en clair', () => {
    expect(formaterDate('2026-10-01T12:00:00Z', maintenant)).toMatch(/^1 oct\./)
  })
  it('date invalide renvoyée telle quelle', () => {
    expect(formaterDate('n/a', maintenant)).toBe('n/a')
  })
})

describe('libellés et composants', () => {
  it('traduit les catégories', () => {
    expect(libelleCategorie('demande_rdv')).toBe('Rendez-vous')
    expect(libelleCategorie('-')).toBe('—')
  })
  it('BadgeEtat applique le ton', () => {
    const w = mount(BadgeEtat, { props: { ton: 'danger' }, slots: { default: 'Urgent' } })
    expect(w.text()).toBe('Urgent')
    expect(w.classes()).toContain('danger')
  })
})
