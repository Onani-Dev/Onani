<template>
  <div class="page-container">
    <h1>Favourites</h1>
    <div v-if="posts.length" class="post-grid">
      <PostThumb v-for="post in posts" :key="post.id" :post="post" />
    </div>
    <p v-else-if="!loading" class="text-muted">You have no favourites yet.</p>
    <Pagination
      :page="page"
      :next-page="nextPage"
      :prev-page="prevPage"
      :per-page="perPage"
      :per-page-options="[20, 40, 50]"
      :total-pages="totalPages"
      @navigate="goToPage"
      @update:perPage="onPerPage"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'
import PostThumb from '@/components/PostThumb.vue'

const posts = ref([])
const page = ref(1)
const perPage = ref(20)
const nextPage = ref(null)
const prevPage = ref(null)
const total = ref(0)
const loading = ref(true)
const totalPages = computed(() => total.value && perPage.value ? Math.ceil(total.value / perPage.value) : null)

async function fetchFavourites() {
  loading.value = true
  try {
    const { data } = await api.get('/posts/favourites', { params: { page: page.value, per_page: perPage.value } })
    posts.value = data.data ?? []
    nextPage.value = data.next_page
    prevPage.value = data.prev_page
    total.value = data.total ?? 0
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  page.value = p
  fetchFavourites()
}

function onPerPage(n) {
  perPage.value = n
  page.value = 1
  fetchFavourites()
}

onMounted(fetchFavourites)
</script>

<style scoped>
.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}
</style>
