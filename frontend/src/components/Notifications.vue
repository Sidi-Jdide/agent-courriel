<script setup lang="ts">
import { useNotifications } from '../composables/notifications'
const { etat, fermer } = useNotifications()
</script>

<template>
  <div class="pile" aria-live="polite">
    <TransitionGroup name="glisse">
      <div v-for="n in etat.liste" :key="n.id" class="notif" :class="n.ton" role="status">
        <span>{{ n.message }}</span>
        <button type="button" aria-label="Fermer" @click="fermer(n.id)">×</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.pile { position: fixed; right: 16px; bottom: 16px; display: flex; flex-direction: column; gap: 8px; z-index: 50; max-width: min(380px, calc(100vw - 32px)); }
.notif {
  display: flex; align-items: flex-start; gap: 12px; padding: 12px 14px; border-radius: var(--rayon);
  background: var(--encre); color: var(--fond); font-size: 14px; box-shadow: 0 8px 24px rgb(0 0 0 / 0.18);
}
.notif.erreur { background: var(--rouge); color: #fff; }
.notif span { flex: 1; }
.notif button { background: none; border: 0; color: inherit; font-size: 18px; line-height: 1; cursor: pointer; opacity: 0.7; padding: 0; }
.glisse-enter-active, .glisse-leave-active { transition: all 0.2s ease; }
.glisse-enter-from, .glisse-leave-to { opacity: 0; transform: translateY(8px); }
</style>
