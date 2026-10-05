<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import Notifications from './components/Notifications.vue'
import { chargerSante, rafraichirStatistiques, tableau } from './composables/tableau'

onMounted(() => {
  chargerSante().catch(() => {})
  rafraichirStatistiques().catch(() => {})
})
</script>

<template>
  <div class="cadre">
    <aside class="menu">
      <RouterLink to="/" class="marque">
        <span class="logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" />
          </svg>
        </span>
        Agent courriel
      </RouterLink>

      <nav class="liens">
        <RouterLink to="/" class="lien" exact-active-class="actif">Tableau de bord</RouterLink>
        <RouterLink :to="{ name: 'courriels', query: { statut: 'en_attente' } }" class="lien"
          :class="{ actif: $route.name === 'courriels' && $route.query.statut === 'en_attente' }">
          À valider
          <span v-if="tableau.stats?.en_attente" class="compteur">{{ tableau.stats.en_attente }}</span>
        </RouterLink>
        <RouterLink :to="{ name: 'courriels' }" class="lien"
          :class="{ actif: ($route.name === 'courriels' && $route.query.statut !== 'en_attente') || $route.name === 'detail' }">
          Historique
        </RouterLink>
      </nav>

      <div class="pied">
        <span v-if="tableau.sante" class="mode" :class="tableau.sante.mode">
          {{ tableau.sante.mode === 'demo' ? 'Mode démo' : 'Gmail connecté' }}
        </span>
        <a href="/docs" target="_blank" rel="noopener" class="doc">Documentation API ↗</a>
      </div>
    </aside>

    <main class="contenu">
      <RouterView />
    </main>
    <Notifications />
  </div>
</template>

<style scoped>
.cadre { display: grid; grid-template-columns: 232px 1fr; min-height: 100vh; }
.menu {
  position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column; gap: 28px;
  padding: 22px 14px; border-right: 1px solid var(--ligne); background: var(--surface);
}
.marque { display: flex; align-items: center; gap: 10px; font-weight: 650; font-size: 16px; padding: 0 8px; letter-spacing: -0.01em; }
.logo { width: 28px; height: 28px; border-radius: 8px; background: var(--accent); display: grid; place-items: center; flex: none; }
.logo svg { width: 16px; height: 16px; stroke: var(--surface); }
.liens { display: flex; flex-direction: column; gap: 2px; }
.lien { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 8px; color: var(--doux); font-weight: 500; font-size: 14px; }
.lien:hover { background: var(--gris-fond); color: var(--encre); }
.lien.actif { background: var(--gris-fond); color: var(--encre); }
.compteur { background: var(--ambre-fond); color: var(--ambre); font-size: 12px; font-weight: 650; padding: 0 8px; border-radius: 99px; font-variant-numeric: tabular-nums; }
.pied { margin-top: auto; display: flex; flex-direction: column; align-items: flex-start; gap: 10px; padding: 0 8px; }
.mode { font-size: 12px; padding: 3px 10px; border-radius: 99px; background: var(--accent-fond); color: var(--accent); }
.mode.demo { background: var(--ambre-fond); color: var(--ambre); }
.doc { font-size: 13px; color: var(--doux); }
.doc:hover { color: var(--encre); }
.contenu { padding: 32px 36px 64px; max-width: 1120px; width: 100%; }

@media (max-width: 820px) {
  .cadre { grid-template-columns: 1fr; }
  .menu {
    position: sticky; height: auto; z-index: 5; flex-direction: row; flex-wrap: wrap; align-items: center;
    gap: 10px 12px; padding: 12px 16px; border-right: 0; border-bottom: 1px solid var(--ligne);
  }
  .marque { padding: 0; font-size: 15px; }
  .pied { margin: 0 0 0 auto; flex-direction: row; align-items: center; padding: 0; }
  .doc { display: none; }
  .liens { flex-direction: row; width: 100%; overflow-x: auto; gap: 4px; order: 3; }
  .lien { white-space: nowrap; gap: 6px; }
  .contenu { padding: 20px 16px 48px; }
}
</style>
