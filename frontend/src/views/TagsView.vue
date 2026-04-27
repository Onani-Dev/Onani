<template>
  <div class="page-container">
    <h1>Tags</h1>
    <div class="sort-controls">
      <label>Sort by:</label>
      <select v-model="sort" @change="onSortChange">
        <option value="post_count">Posts</option>
        <option value="name">Name</option>
        <option value="type">Type</option>
      </select>
      <button class="order-btn" @click="toggleOrder">{{ order === 'asc' ? '↑ Asc' : '↓ Desc' }}</button>
    </div>
    <table v-if="tags.length" class="tag-table">
      <thead><tr><th>Name</th><th>Type</th><th>Posts</th></tr></thead>
      <tbody>
        <tr v-for="tag in tags" :key="tag.id">
          <td><router-link :to="`/tags/${tag.id}`">{{ tag.name }}</router-link></td>
          <td>{{ tag.type }}</td>
          <td>{{ tag.post_count }}</td>
        </tr>
      </tbody>
    </table>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" :per-page="perPage" :total-pages="totalPages" @navigate="goToPage" @update:perPage="onPerPage" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'

const tags = ref([])
const page = ref(1)
const nextPage = ref(null)
const prevPage = ref(null)
const total = ref(0)
const sort = ref('post_count')
const order = ref('desc')
const perPage = ref(30)
const totalPages = computed(() => total.value && perPage.value ? Math.ceil(total.value / perPage.value) : null)

async function fetchTags() {
  const { data } = await api.get('/tags', { params: { page: page.value, per_page: perPage.value, sort: sort.value, order: order.value, min_posts: 1 } })
  tags.value = data.data
  nextPage.value = data.next_page
  prevPage.value = data.prev_page
  total.value = data.total ?? 0
}

function onSortChange() {
  order.value = sort.value === 'name' ? 'asc' : 'desc'
  page.value = 1
  fetchTags()
}

function toggleOrder() {
  order.value = order.value === 'asc' ? 'desc' : 'asc'
  page.value = 1
  fetchTags()
}

function goToPage(p) { page.value = p; fetchTags() }

function onPerPage(n) { perPage.value = n; page.value = 1; fetchTags() }

onMounted(fetchTags)
</script>

<style scoped>
.sort-controls { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.order-btn {
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  padding: 4px 10px;
  font-size: 0.875rem;
  border-radius: 4px;
}
.order-btn:hover { background: var(--item-hover); }
.tag-table { width: 100%; border-collapse: collapse; }
.tag-table th, .tag-table td { text-align: left; padding: 0.4rem 0.75rem; border-bottom: 1px solid #333; }
.tag-table a { color: #8af; }
</style>
