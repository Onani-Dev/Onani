<template>
  <div class="posts-container">
    <h1>Posts</h1>
    <form class="search-bar" @submit.prevent="search">
      <input v-model="tagQuery" placeholder="Search by tags..." />
      <button type="submit">Search</button>
    </form>
    <div v-if="posts.length" class="post-grid">
      <router-link v-for="post in posts" :key="post.id" :to="`/posts/${post.id}`" class="post-thumb">
        <img :src="`/images/thumbnail/${post.filename}?size=large`" :alt="`Post #${post.id}`" loading="lazy" />
      </router-link>
    </div>
    <p v-else-if="!loading">No posts found.</p>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" @navigate="goToPage" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'

const route = useRoute()
const router = useRouter()

const posts = ref([])
const loading = ref(true)
const tagQuery = ref(route.query.tags || '')
const page = ref(Number(route.query.page) || 1)
const nextPage = ref(null)
const prevPage = ref(null)

async function fetchPosts() {
  loading.value = true
  try {
    const params = { page: page.value, per_page: 30 }
    if (tagQuery.value) params.tags = tagQuery.value
    const { data } = await api.get('/posts', { params })
    posts.value = data.data
    nextPage.value = data.next_page
    prevPage.value = data.prev_page
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  router.push({ query: { tags: tagQuery.value || undefined, page: undefined } })
}

function goToPage(p) {
  page.value = p
  router.push({ query: { ...route.query, page: p } })
}

watch(() => route.query, () => {
  page.value = Number(route.query.page) || 1
  tagQuery.value = route.query.tags || ''
  fetchPosts()
})

onMounted(fetchPosts)
</script>

<style scoped>
.posts-container {
  background-color: var(--bg-raised);
  padding: 10px 10px 1.5em 10px;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 50vh;
}
.posts-container h1 {
  margin: 0.5em;
}
.search-bar {
  display: flex;
  gap: 0.5rem;
  margin: 0 0.5em 1em 0.5em;
}
.search-bar input {
  flex: 1;
  text-align: left;
}

@media (max-width: 689px) {
  .posts-container {
    margin-right: auto;
    margin-left: auto;
    padding: 0;
  }
}
</style>
