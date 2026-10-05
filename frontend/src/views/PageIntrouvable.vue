<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="carte vide">
    <h1>Page introuvable</h1>
    <p>Cette adresse n'existe pas.</p>
    <RouterLink to="/" class="bouton principal">Retour au tableau de bord</RouterLink>
  </div>
</template>

<style scoped>
.vide { text-align: center; padding: 48px 18px; }
.vide p { color: var(--doux); margin: 8px 0 20px; }
</style>
