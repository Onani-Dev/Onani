<template>
  <div class="page-container">
    <h1>News</h1>
    <article v-for="a in articles" :key="a.id" class="news-card">
      <router-link :to="`/news/${a.id}`"><h2>{{ a.title }}</h2></router-link>
      <p class="meta">{{ a.type }} · {{ a.created_at }}</p>
    </article>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" @navigate="goToPage" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'

const articles = ref([])
const page = ref(1)
const nextPage = ref(null)
const prevPage = ref(null)

async function fetchNews() {
  const { data } = await api.get('/news', { params: { page: page.value } })
  articles.value = data.data
  nextPage.value = data.next_page
  prevPage.value = data.prev_page
}

function goToPage(p) { page.value = p; fetchNews() }

onMounted(fetchNews)
</script>

<style scoped>
.news-card { margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #333; }
.news-card h2 { margin: 0; }
.news-card a { color: #8af; text-decoration: none; }
.meta { color: #999; font-size: 0.85rem; }
</style>
