<template>
  <div class="page-container">
    <h1>Tags</h1>
    <div class="sort-controls">
      <label>Sort by:</label>
      <select v-model="sort" @change="fetchTags">
        <option value="post_count">Posts</option>
        <option value="name">Name</option>
        <option value="type">Type</option>
      </select>
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
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" @navigate="goToPage" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'

const tags = ref([])
const page = ref(1)
const nextPage = ref(null)
const prevPage = ref(null)
const sort = ref('post_count')

async function fetchTags() {
  const { data } = await api.get('/tags', { params: { page: page.value, per_page: 30, sort: sort.value, order: 'desc' } })
  tags.value = data.data
  nextPage.value = data.next_page
  prevPage.value = data.prev_page
}

function goToPage(p) { page.value = p; fetchTags() }

onMounted(fetchTags)
</script>

<style scoped>
.sort-controls { margin-bottom: 1rem; }
.tag-table { width: 100%; border-collapse: collapse; }
.tag-table th, .tag-table td { text-align: left; padding: 0.4rem 0.75rem; border-bottom: 1px solid #333; }
.tag-table a { color: #8af; }
</style>
