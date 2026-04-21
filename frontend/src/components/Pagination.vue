<template>
  <div v-if="nextPage || prevPage || perPage != null" class="pagination">
    <button :disabled="page === 1" @click="$emit('navigate', 1)" title="First page">«</button>
    <button :disabled="!prevPage" @click="$emit('navigate', prevPage)">‹ Prev</button>
    <form class="page-jump" @submit.prevent="commitJump">
      <span>Page</span>
      <input
        v-model.number="jumpVal"
        type="number"
        :min="1"
        :max="totalPages || undefined"
        class="page-input"
        @focus="jumpVal = page"
      />
      <template v-if="totalPages"> of {{ totalPages }}</template>
    </form>
    <button :disabled="!nextPage" @click="$emit('navigate', nextPage)">Next ›</button>
    <button v-if="totalPages" :disabled="page === totalPages" @click="$emit('navigate', totalPages)" title="Last page">»</button>
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
import { ref, watch } from 'vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  nextPage: { type: Number, default: null },
  prevPage: { type: Number, default: null },
  perPage: { type: Number, default: null },
  perPageOptions: { type: Array, default: () => [30, 60, 100] },
  totalPages: { type: Number, default: null },
})

const emit = defineEmits(['navigate', 'update:perPage'])

const jumpVal = ref(props.page)
watch(() => props.page, v => { jumpVal.value = v })

function commitJump() {
  const p = Math.max(1, props.totalPages ? Math.min(jumpVal.value, props.totalPages) : jumpVal.value)
  if (p !== props.page) emit('navigate', p)
}
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0;
  justify-content: center;
  flex-wrap: wrap;
}
.pagination button {
  padding: 0.4rem 0.75rem;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: default; }
.page-jump {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
}
.page-input {
  width: 3.5em;
  text-align: center;
  padding: 0.3em 0.2em;
  font-size: 0.9rem;
}
.per-page-select {
  margin-left: 0.25rem;
  font-size: 0.875rem;
}
</style>
