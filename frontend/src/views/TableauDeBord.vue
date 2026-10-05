<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ListeCourriels from '../components/ListeCourriels.vue'
import { api, ErreurApi } from '../api'
import { useNotifications } from '../composables/notifications'
import { rafraichirStatistiques, tableau } from '../composables/tableau'
import { ACTIONS, libelleCategorie } from '../libelles'
import type { Courriel } from '../types'

const { notifier } = useNotifications()
const aValider = ref<Courriel[]>([])
const recents = ref<Courriel[]>([])
const chargement = ref(true)
const enCours = ref(false)

const stats = computed(() => tableau.stats)
const maxCategorie = computed(() => Math.max(1, ...Object.values(stats.value?.par_categorie ?? {})))
const tuiles = computed(() => {
  const s = stats.value
  const a = s?.par_action ?? {}
  return [
    { libelle: 'À valider', valeur: s?.en_attente, accent: true, lien: { name: 'courriels', query: { statut: 'en_attente' } } },
    { libelle: 'Courriels traités', valeur: s?.total, lien: { name: 'courriels' } },
    { libelle: 'Envoyés automatiquement', valeur: a['envoyé'] ?? (s ? 0 : undefined), lien: { name: 'courriels', query: { action: 'envoyé' } } },
    { libelle: 'Ignorés ou classés', valeur: s ? (a['ignoré'] ?? 0) + (a['classé'] ?? 0) : undefined, lien: { name: 'courriels', query: { action: 'ignoré' } } },
  ]
})

async function charger() {
  chargement.value = true
  try {
    const [attente, derniers] = await Promise.all([
      api.courriels({ statut: 'en_attente', taille: 5 }),
      api.courriels({ taille: 5 }),
      rafraichirStatistiques(),
    ])
    aValider.value = attente.elements
    recents.value = derniers.elements
  } catch (e) {
    notifier(e instanceof ErreurApi ? e.message : 'Chargement impossible.', 'erreur')
  } finally {
    chargement.value = false
  }
}

async function lancerPassage() {
  enCours.value = true
  try {
    const { bilan } = await api.lancerCycle()
    const parties = Object.entries(bilan).map(([action, n]) => `${n} ${(ACTIONS[action] ?? action).toLowerCase()}`)
    notifier(parties.length ? `Passage terminé : ${parties.join(', ')}.` : 'Aucun nouveau courriel.')
    await charger()
  } catch (e) {
    notifier(e instanceof ErreurApi ? e.message : 'Le passage a échoué.', 'erreur')
  } finally {
    enCours.value = false
  }
}

onMounted(charger)
</script>

<template>
  <header class="entete-page">
    <div>
      <h1>Tableau de bord</h1>
      <p>Ce que l'agent a fait, et ce qui attend votre validation.</p>
    </div>
    <button class="bouton principal" :disabled="enCours" @click="lancerPassage">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
        stroke-linecap="round" stroke-linejoin="round" :class="{ tourne: enCours }" aria-hidden="true">
        <path d="M21 12a9 9 0 1 1-2.6-6.4" /><path d="M21 3v6h-6" />
      </svg>
      {{ enCours ? 'Analyse en cours…' : 'Vérifier la boîte' }}
    </button>
  </header>

  <section class="tuiles">
    <RouterLink v-for="t in tuiles" :key="t.libelle" :to="t.lien" class="carte tuile" :class="{ accent: t.accent }">
      <div class="chiffre">
        <template v-if="t.valeur !== undefined">{{ t.valeur }}</template>
        <span v-else class="squelette" style="display: inline-block; width: 40px; height: 28px" />
      </div>
      <div class="etiquette">{{ t.libelle }}</div>
    </RouterLink>
  </section>

  <div class="grille">
    <section>
      <div class="titre-section">
        <h2 class="surtitre">À valider</h2>
        <RouterLink :to="{ name: 'courriels', query: { statut: 'en_attente' } }" class="voir">Tout voir →</RouterLink>
      </div>
      <ListeCourriels :courriels="aValider" :chargement="chargement" vide="Rien à valider. Tout est à jour." />

      <div class="titre-section" style="margin-top: 28px">
        <h2 class="surtitre">Activité récente</h2>
        <RouterLink :to="{ name: 'courriels' }" class="voir">Historique →</RouterLink>
      </div>
      <ListeCourriels :courriels="recents" :chargement="chargement" />
    </section>

    <section class="carte">
      <h2 class="surtitre">Par catégorie</h2>
      <div class="barres">
        <RouterLink v-for="(n, cat) in stats?.par_categorie" :key="cat" class="barre"
          :to="{ name: 'courriels', query: { categorie: cat } }">
          <div class="nom"><span>{{ libelleCategorie(String(cat)) }}</span><span>{{ n }}</span></div>
          <div class="piste"><div class="rempli" :style="{ width: `${(n / maxCategorie) * 100}%` }" /></div>
        </RouterLink>
        <p v-if="stats && !Object.keys(stats.par_categorie).length" class="aucun">Aucune donnée pour l'instant.</p>
      </div>
      <p v-if="tableau.sante" class="config">
        Envoi automatique : <strong>{{ tableau.sante.envoi_auto ? 'activé' : 'désactivé (brouillons)' }}</strong>
      </p>
    </section>
  </div>
</template>

<style scoped>
.tuiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 28px; }
.tuile { padding: 16px 18px; transition: border-color 0.15s; }
.tuile:hover { border-color: var(--doux); }
.chiffre { font-size: 30px; font-weight: 650; letter-spacing: -0.02em; line-height: 1.15; font-variant-numeric: tabular-nums; }
.etiquette { color: var(--doux); font-size: 13px; margin-top: 4px; }
.tuile.accent { background: var(--ambre-fond); border-color: color-mix(in srgb, var(--ambre) 45%, transparent); }
.tuile.accent .chiffre, .tuile.accent .etiquette { color: var(--ambre); }
.grille { display: grid; grid-template-columns: minmax(0, 2fr) minmax(240px, 1fr); gap: 20px; align-items: start; }
.titre-section { display: flex; justify-content: space-between; align-items: baseline; }
.voir { font-size: 13px; color: var(--accent); font-weight: 550; }
.barres { display: grid; gap: 12px; }
.nom { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 5px; }
.nom span:last-child { color: var(--doux); font-variant-numeric: tabular-nums; }
.piste { height: 6px; border-radius: 99px; background: var(--gris-fond); }
.rempli { height: 100%; border-radius: 99px; background: var(--accent); transition: width 0.4s ease; }
.barre:hover .rempli { filter: brightness(1.15); }
.aucun { color: var(--doux); margin: 0; font-size: 14px; }
.config { margin: 20px 0 0; padding-top: 14px; border-top: 1px solid var(--ligne); font-size: 13px; color: var(--doux); }
.config strong { color: var(--encre); font-weight: 600; }
.tourne { animation: tourner 0.9s linear infinite; }
@keyframes tourner { to { transform: rotate(360deg); } }
@media (max-width: 960px) {
  .tuiles { grid-template-columns: repeat(2, 1fr); }
  .grille { grid-template-columns: 1fr; }
}
@media (max-width: 480px) { .chiffre { font-size: 26px; } }
</style>
