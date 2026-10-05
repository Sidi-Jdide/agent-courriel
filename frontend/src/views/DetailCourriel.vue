<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import BadgeEtat from '../components/BadgeEtat.vue'
import { api, ErreurApi } from '../api'
import { useNotifications } from '../composables/notifications'
import { rafraichirStatistiques } from '../composables/tableau'
import { ACTIONS, etatCourriel, formaterDate, libelleCategorie } from '../libelles'
import type { Courriel } from '../types'

const props = defineProps<{ id: string }>()
const router = useRouter()
const { notifier } = useNotifications()

const courriel = ref<Courriel | null>(null)
const texte = ref('')
const erreur = ref('')
const action = ref<'approuver' | 'rejeter' | null>(null)

const enAttente = computed(() => courriel.value?.statut === 'en_attente' && !!courriel.value.brouillon_id)
const modifie = computed(() => texte.value.trim() !== (courriel.value?.reponse ?? '').trim())

watch(() => props.id, async (id) => {
  courriel.value = null
  erreur.value = ''
  try {
    courriel.value = await api.courriel(id)
    texte.value = courriel.value.reponse ?? ''
  } catch (e) {
    erreur.value = e instanceof ErreurApi ? e.message : 'Chargement impossible.'
  }
}, { immediate: true })

async function decider(choix: 'approuver' | 'rejeter') {
  if (!courriel.value) return
  if (choix === 'rejeter' && !confirm('Rejeter ce brouillon ? Il sera supprimé de Gmail.')) return
  action.value = choix
  try {
    courriel.value = choix === 'approuver'
      ? await api.approuver(courriel.value.id, modifie.value ? texte.value : undefined)
      : await api.rejeter(courriel.value.id)
    notifier(choix === 'approuver' ? `Réponse envoyée à ${courriel.value.expediteur}.` : 'Brouillon rejeté.')
    rafraichirStatistiques().catch(() => {})
    router.push({ name: 'courriels', query: { statut: 'en_attente' } })
  } catch (e) {
    notifier(e instanceof ErreurApi ? e.message : 'Action impossible.', 'erreur')
  } finally {
    action.value = null
  }
}
</script>

<template>
  <RouterLink :to="{ name: 'courriels' }" class="retour" @click.prevent="router.back()">← Retour</RouterLink>

  <p v-if="erreur" class="carte erreur">{{ erreur }}</p>

  <template v-else-if="courriel">
    <header class="entete">
      <h1>{{ courriel.sujet }}</h1>
      <div class="badges">
        <BadgeEtat :ton="etatCourriel(courriel).ton">{{ etatCourriel(courriel).libelle }}</BadgeEtat>
        <BadgeEtat v-if="courriel.priorite === 'haute'" ton="danger">Urgent</BadgeEtat>
        <BadgeEtat ton="neutre">{{ libelleCategorie(courriel.categorie) }}</BadgeEtat>
      </div>
    </header>

    <div class="grille">
      <section class="carte">
        <dl>
          <div><dt>De</dt><dd>{{ courriel.expediteur }}</dd></div>
          <div><dt>Reçu</dt><dd>{{ formaterDate(courriel.date) }}</dd></div>
          <div><dt>Action de l'agent</dt><dd>{{ ACTIONS[courriel.action] ?? courriel.action }}</dd></div>
          <div v-if="courriel.resume"><dt>Résumé</dt><dd>{{ courriel.resume }}</dd></div>
          <div><dt>Pourquoi cette décision</dt><dd>{{ courriel.raison }}</dd></div>
        </dl>
      </section>

      <section class="carte">
        <template v-if="enAttente">
          <h2 class="surtitre">Réponse proposée</h2>
          <p class="aide">Modifiez le texte au besoin. En approuvant, la réponse part dans le même fil Gmail.</p>
          <textarea v-model="texte" class="champ" aria-label="Réponse" :disabled="!!action" />
          <div class="actions">
            <button class="bouton principal" :disabled="!!action || !texte.trim()" @click="decider('approuver')">
              {{ action === 'approuver' ? 'Envoi…' : modifie ? 'Envoyer la version modifiée' : 'Approuver et envoyer' }}
            </button>
            <button class="bouton secondaire" :disabled="!!action" @click="decider('rejeter')">Rejeter</button>
            <span v-if="modifie" class="modifie">Modifié</span>
          </div>
        </template>
        <template v-else-if="courriel.reponse">
          <h2 class="surtitre">{{ courriel.statut === 'rejeté' ? 'Réponse rejetée' : 'Réponse envoyée' }}</h2>
          <pre class="texte">{{ courriel.reponse }}</pre>
        </template>
        <template v-else>
          <h2 class="surtitre">Réponse</h2>
          <p class="aide" style="margin: 0">Aucune réponse : ce courriel n'en demandait pas.</p>
        </template>
      </section>
    </div>
  </template>

  <div v-else class="carte" aria-busy="true">
    <div class="squelette" style="height: 26px; width: 60%" />
    <div class="squelette" style="height: 14px; width: 35%; margin-top: 14px" />
  </div>
</template>

<style scoped>
.retour { display: inline-block; color: var(--doux); font-size: 14px; margin-bottom: 16px; }
.retour:hover { color: var(--encre); }
.erreur { color: var(--rouge); }
.entete { margin-bottom: 20px; }
.badges { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.grille { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.6fr); gap: 16px; align-items: start; }
dl { margin: 0; display: grid; gap: 14px; }
dt { color: var(--doux); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
dd { margin: 2px 0 0; overflow-wrap: anywhere; }
.aide { color: var(--doux); font-size: 13px; margin: 0 0 10px; }
textarea, .texte { width: 100%; font: 14px/1.65 var(--police); background: var(--fond); padding: 14px; white-space: pre-wrap; margin: 0; border: 1px solid var(--ligne); border-radius: 8px; }
textarea { min-height: 300px; resize: vertical; }
.actions { display: flex; align-items: center; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
.modifie { font-size: 12px; color: var(--ambre); }
@media (max-width: 820px) { .grille { grid-template-columns: 1fr; } }
</style>
