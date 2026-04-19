<template>
  <div class="page-container">
    <h1>Favourites</h1>
    <div v-if="posts.length" class="post-grid">
      <router-link
        v-for="post in posts"
        :key="post.id"
        :to="`/posts/${post.id}`"
        class="post-thumb"
      >
        <img
          :src="post.thumbnail_url"
          :alt="`Post #${post.id}`"
          loading="lazy"
          :class="{ 'sfw-blurred': shouldBlur(post) }"
        />
        <div v-if="shouldBlur(post)" class="sfw-overlay" @click.stop="reveal(post.id)">Show</div>
      </router-link>
    </div>
    <p v-else-if="!loading" class="text-muted">You have no favourites yet.</p>
    <Pagination
      :page="page"
      :next-page="nextPage"
      :prev-page="prevPage"
      @navigate="goToPage"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'
import { useSfwMode } from '@/composables/useSfwMode'

const { shouldBlur, reveal } = useSfwMode()
const posts = ref([])
const page = ref(1)
const nextPage = ref(null)
const prevPage = ref(null)
const loading = ref(true)

async function fetchFavourites() {
  loading.value = true
  try {
    const { data } = await api.get('/posts/favourites', { params: { page: page.value } })
    posts.value = data.data ?? []
    nextPage.value = data.next_page
    prevPage.value = data.prev_page
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  page.value = p
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
.post-thumb { position: relative; display: block; }
.post-thumb img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 6px; }
.sfw-blurred { filter: blur(16px); }
.sfw-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  cursor: pointer;
  border-radius: 6px;
}
</style>
