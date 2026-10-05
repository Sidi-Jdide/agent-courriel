<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ListeCourriels from '../components/ListeCourriels.vue'
import { api, ErreurApi } from '../api'
import { useNotifications } from '../composables/notifications'
import { CATEGORIES } from '../libelles'
import type { PageCourriels } from '../types'

const TAILLE = 15
const route = useRoute()
const router = useRouter()
const { notifier } = useNotifications()

const resultat = ref<PageCourriels | null>(null)
const chargement = ref(false)
const recherche = ref(String(route.query.q ?? ''))

// Les filtres vivent dans l'URL : partageable, et le bouton « précédent » fonctionne.
const filtres = computed(() => ({
  action: route.query.action as string | undefined,
  statut: route.query.statut as string | undefined,
  categorie: route.query.categorie as string | undefined,
  q: route.query.q as string | undefined,
  page: Number(route.query.page ?? 1),
}))
const pages = computed(() => Math.max(1, Math.ceil((resultat.value?.total ?? 0) / TAILLE)))

type FiltrePuce = { statut?: string; action?: string }
const PUCES: { libelle: string; query: FiltrePuce }[] = [
  { libelle: 'Tous', query: {} },
  { libelle: 'À valider', query: { statut: 'en_attente' } },
  { libelle: 'Approuvés', query: { statut: 'approuvé' } },
  { libelle: 'Envoyés auto', query: { action: 'envoyé' } },
  { libelle: 'Rejetés', query: { statut: 'rejeté' } },
  { libelle: 'Classés', query: { action: 'classé' } },
  { libelle: 'Ignorés', query: { action: 'ignoré' } },
]
const puceActive = (q: FiltrePuce) => q.statut === filtres.value.statut && q.action === filtres.value.action

function changer(nouveaux: Record<string, string | number | undefined>) {
  const query = { ...route.query, ...nouveaux, page: undefined } as Record<string, unknown>
  for (const cle of Object.keys(query)) if (query[cle] === undefined || query[cle] === '') delete query[cle]
  router.push({ query: query as Record<string, string> })
}
function choisirPuce(q: FiltrePuce) {
  changer({ statut: q.statut, action: q.action })
}
function allerPage(p: number) {
  router.push({ query: { ...route.query, page: p > 1 ? String(p) : undefined } })
}

let minuterie: ReturnType<typeof setTimeout> | undefined
watch(recherche, (texte) => {
  clearTimeout(minuterie)
  minuterie = setTimeout(() => changer({ q: texte.trim() || undefined }), 300)
})

async function charger() {
  chargement.value = true
  try {
    resultat.value = await api.courriels({ ...filtres.value, taille: TAILLE })
  } catch (e) {
    notifier(e instanceof ErreurApi ? e.message : 'Chargement impossible.', 'erreur')
  } finally {
    chargement.value = false
  }
}
watch(filtres, charger, { immediate: true, deep: true })
</script>

<template>
  <header class="entete-page">
    <div>
      <h1>{{ filtres.statut === 'en_attente' ? 'À valider' : 'Historique' }}</h1>
      <p v-if="resultat">{{ resultat.total }} courriel{{ resultat.total > 1 ? 's' : '' }}</p>
    </div>
  </header>

  <nav class="puces" aria-label="Filtrer par état">
    <button v-for="p in PUCES" :key="p.libelle" type="button" class="puce"
      :class="{ active: puceActive(p.query) }" @click="choisirPuce(p.query)">{{ p.libelle }}</button>
  </nav>

  <div class="outils">
    <input v-model="recherche" type="search" class="champ recherche" placeholder="Rechercher un expéditeur, un sujet…"
      aria-label="Rechercher" />
    <select class="champ" :value="filtres.categorie ?? ''" aria-label="Catégorie"
      @change="changer({ categorie: ($event.target as HTMLSelectElement).value || undefined })">
      <option value="">Toutes catégories</option>
      <option v-for="(libelle, cle) in CATEGORIES" :key="cle" :value="cle">{{ libelle }}</option>
    </select>
  </div>

  <ListeCourriels :courriels="resultat?.elements ?? []" :chargement="chargement"
    vide="Aucun courriel ne correspond à ces filtres." />

  <nav v-if="pages > 1" class="pagination" aria-label="Pagination">
    <button class="bouton secondaire" :disabled="filtres.page <= 1" @click="allerPage(filtres.page - 1)">← Précédent</button>
    <span>Page {{ filtres.page }} sur {{ pages }}</span>
    <button class="bouton secondaire" :disabled="filtres.page >= pages" @click="allerPage(filtres.page + 1)">Suivant →</button>
  </nav>
</template>

<style scoped>
.puces { display: flex; gap: 8px; margin-bottom: 14px; overflow-x: auto; padding-bottom: 2px; }
.puce { font-size: 13px; padding: 6px 13px; border-radius: 99px; border: 1px solid var(--ligne); background: var(--surface); color: var(--doux); cursor: pointer; white-space: nowrap; }
.puce:hover { color: var(--encre); }
.puce.active { background: var(--encre); color: var(--fond); border-color: var(--encre); }
.outils { display: flex; gap: 8px; margin-bottom: 14px; }
.recherche { flex: 1; min-width: 0; }
.pagination { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 16px; color: var(--doux); font-size: 14px; }
@media (max-width: 520px) { .outils { flex-direction: column; } }
</style>
