<template>
  <div v-if="nextPage || prevPage || perPage != null" class="pagination">
    <button :disabled="!prevPage" @click="$emit('navigate', prevPage)">← Prev</button>
    <span class="page-info">Page {{ page }}</span>
    <button :disabled="!nextPage" @click="$emit('navigate', nextPage)">Next →</button>
    <select
      v-if="perPage != null"
      class="per-page-select"
      :value="perPage"
      @change="$emit('update:perPage', Number($event.target.value))"
    >
      <option v-for="opt in perPageOptions" :key="opt" :value="opt">{{ opt }} / page</option>
    </select>
  </div>
</template>

<script setup>
defineProps({
  page: { type: Number, default: 1 },
  nextPage: { type: Number, default: null },
  prevPage: { type: Number, default: null },
  perPage: { type: Number, default: null },
  perPageOptions: { type: Array, default: () => [30, 60, 100] },
})

defineEmits(['navigate', 'update:perPage'])
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
.per-page-select {
  margin-left: 0.5rem;
  font-size: 0.875rem;
}
</style>
