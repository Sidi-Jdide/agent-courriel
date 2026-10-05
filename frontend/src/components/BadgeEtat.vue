<script setup lang="ts">
import type { Ton } from '../libelles'
defineProps<{ ton: Ton }>()
</script>

<template>
  <span class="badge" :class="ton"><slot /></span>
</template>

<style scoped>
.badge { display: inline-block; font-size: 12px; font-weight: 550; padding: 2px 9px; border-radius: 99px; white-space: nowrap; }
.attention { background: var(--ambre-fond); color: var(--ambre); }
.succes { background: var(--accent-fond); color: var(--accent); }
.neutre { background: var(--gris-fond); color: var(--doux); }
.danger { background: var(--rouge-fond); color: var(--rouge); }
</style>
