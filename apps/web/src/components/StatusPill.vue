<script setup lang="ts">
defineProps<{ label: string; status: string }>()

function tone(status: string) {
  if (['settled', 'completed'].includes(status)) return 'teal'
  if (['pending_publicity', 'pending_advance', 'pending_full', 'pending_ratio', 'pending_first_payout', 'pending_final_payout'].includes(status)) return 'amber'
  if (['cancelled'].includes(status)) return 'red'
  if (['partial_paid'].includes(status)) return 'blue'
  return ''
}
</script>

<template>
  <span class="status-pill" :class="tone(status)">{{ label }}</span>
</template>
