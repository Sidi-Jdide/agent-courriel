<script setup lang="ts">
import { RouterLink } from 'vue-router'
import BadgeEtat from './BadgeEtat.vue'
import { etatCourriel, formaterDate } from '../libelles'
import type { Courriel } from '../types'

defineProps<{ courriels: Courriel[]; chargement?: boolean; vide?: string }>()
</script>

<template>
  <div class="liste carte">
    <template v-if="chargement && !courriels.length">
      <div v-for="i in 4" :key="i" class="ligne">
        <div class="squelette" style="height: 14px; width: 40%" />
        <div class="squelette" style="height: 14px; width: 70%; margin-top: 8px" />
      </div>
    </template>
    <RouterLink v-for="c in courriels" :key="c.id" :to="{ name: 'detail', params: { id: c.id } }" class="ligne"
      :class="{ estompe: chargement }">
      <div class="exp">{{ c.expediteur }}</div>
      <div class="sujet">{{ c.sujet }}</div>
      <div class="resume">{{ c.resume || c.raison }}</div>
      <div class="droite">
        <time class="date" :datetime="c.date">{{ formaterDate(c.date) }}</time>
        <BadgeEtat :ton="etatCourriel(c).ton">{{ etatCourriel(c).libelle }}</BadgeEtat>
        <BadgeEtat v-if="c.priorite === 'haute'" ton="danger">Urgent</BadgeEtat>
      </div>
    </RouterLink>
    <p v-if="!chargement && !courriels.length" class="vide">{{ vide ?? 'Aucun courriel.' }}</p>
  </div>
</template>

<style scoped>
.liste { padding: 0; overflow: hidden; }
.ligne { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 16px; padding: 14px 18px; border-top: 1px solid var(--ligne); transition: background 0.12s, opacity 0.12s; }
.ligne:first-child { border-top: 0; }
a.ligne:hover { background: var(--fond); }
.estompe { opacity: 0.55; }
.exp { font-weight: 600; font-size: 14px; }
.sujet { font-size: 14px; }
.resume { color: var(--doux); font-size: 13px; }
.exp, .sujet, .resume { grid-column: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.droite { grid-row: 1 / span 3; grid-column: 2; display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.date { color: var(--doux); font-size: 12px; white-space: nowrap; }
.vide { margin: 0; padding: 40px 18px; text-align: center; color: var(--doux); }
</style>
