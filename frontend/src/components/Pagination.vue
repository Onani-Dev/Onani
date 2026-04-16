<template>
  <div v-if="nextPage || prevPage" class="pagination">
    <button :disabled="!prevPage" @click="$emit('navigate', prevPage)">← Prev</button>
    <span class="page-info">Page {{ page }}</span>
    <button :disabled="!nextPage" @click="$emit('navigate', nextPage)">Next →</button>
  </div>
</template>

<script setup>
defineProps({
  page: { type: Number, default: 1 },
  nextPage: { type: Number, default: null },
  prevPage: { type: Number, default: null },
})

defineEmits(['navigate'])
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
  justify-content: center;
}
.pagination button {
  padding: 0.4rem 1rem;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: default; }
</style>
