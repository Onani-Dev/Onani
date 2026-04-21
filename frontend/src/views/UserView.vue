<template>
  <div v-if="user" class="page-container">
    <div class="user-header">
      <img v-if="user.settings?.avatar" :src="user.settings.avatar" class="avatar-lg" />
      <div>
        <h1>{{ user.nickname || user.username }}</h1>
        <p v-if="user.settings?.biography">{{ user.settings.biography }}</p>
        <p class="meta">{{ user.post_count }} posts · Joined {{ user.created_at }}</p>
      </div>
    </div>
    <h2>Posts</h2>
    <div v-if="posts.length" class="post-grid">
      <PostThumb v-for="post in posts" :key="post.id" :post="post" />
    </div>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" @navigate="goToPage" />
  </div>
  <p v-else>Loading...</p>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'
import PostThumb from '@/components/PostThumb.vue'

const props = defineProps({ id: [String, Number] })
const user = ref(null)
const posts = ref([])
const page = ref(1)
const nextPage = ref(null)
const prevPage = ref(null)

async function fetchUser() {
  const { data } = await api.get('/users', { params: { id: props.id } })
  user.value = data
}

async function fetchPosts() {
  const { data } = await api.get('/users/posts', { params: { user_id: props.id, page: page.value } })
  posts.value = data.data
  nextPage.value = data.next_page
  prevPage.value = data.prev_page
}

function goToPage(p) { page.value = p; fetchPosts() }

onMounted(async () => {
  await fetchUser()
  await fetchPosts()
})
</script>

<style scoped>
.user-header { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.5rem; }
.avatar-lg { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; }
.meta { color: #999; font-size: 0.9rem; }
.post-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; }
</style>
