import { reactive } from 'vue'
import { api } from '../api'
import type { Sante, Statistiques } from '../types'

/** État partagé : statistiques (compteur « À valider » du menu) et infos du serveur. */
export const tableau = reactive<{ stats: Statistiques | null; sante: Sante | null }>({
  stats: null,
  sante: null,
})

export async function rafraichirStatistiques() {
  tableau.stats = await api.statistiques()
}

export async function chargerSante() {
  tableau.sante = await api.sante()
}
