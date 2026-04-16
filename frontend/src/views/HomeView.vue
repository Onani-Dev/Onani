<template>
  <div class="home">
    <div class="index-post-group">
      <div class="post-group-header">
        <h2>Recent Posts</h2>
        <router-link to="/posts">View All →</router-link>
      </div>
      <div v-if="posts.length" class="post-group-grid">
        <router-link v-for="post in posts" :key="post.id" :to="`/posts/${post.id}`" class="post-thumb">
          <img :src="`/images/thumbnail/${post.filename}?size=large`" :alt="`Post #${post.id}`" loading="lazy" />
        </router-link>
      </div>
      <div v-else-if="!loading" class="post-group-grid">
        <p>No posts yet.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'

const posts = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/posts', { params: { per_page: 7 } })
    posts.value = data.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.index-post-group {
  margin-bottom: 1em;
}
.post-group-header {
  padding: 10px;
  background-color: var(--header-bg);
  border-radius: 15px 15px 0 0;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}
.post-group-header a {
  color: var(--text-muted);
}
.post-group-grid {
  background-color: var(--bg-overlay);
  padding: 10px 10px 1.5em 10px;
  min-height: 10em;
  border-radius: 0 0 15px 15px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(11em, 1fr));
}

@media (max-width: 689px) {
  .post-group-grid {
    grid-template-columns: repeat(auto-fill, minmax(6em, 1fr));
  }
}
@media (min-width: 690px) and (max-width: 1110px) {
  .post-group-grid {
    grid-template-columns: repeat(auto-fill, minmax(9em, 1fr));
  }
}
</style>
