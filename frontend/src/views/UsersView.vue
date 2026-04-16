<template>
  <div class="page-container">
    <h1>Users</h1>
    <div v-if="users.length" class="user-list">
      <router-link v-for="u in users" :key="u.id" :to="`/users/${u.id}`" class="user-card">
        <img v-if="u.settings?.avatar" :src="u.settings.avatar" class="avatar" />
        <div>
          <strong>{{ u.nickname || u.username }}</strong>
          <span class="meta">{{ u.post_count }} posts</span>
        </div>
      </router-link>
    </div>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" @navigate="goToPage" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'

const users = ref([])
const page = ref(1)
const nextPage = ref(null)
const prevPage = ref(null)

async function fetchUsers() {
  const { data } = await api.get('/users', { params: { page: page.value } })
  users.value = data.data
  nextPage.value = data.next_page
  prevPage.value = data.prev_page
}

function goToPage(p) { page.value = p; fetchUsers() }

onMounted(fetchUsers)
</script>

<style scoped>
.user-list { display: flex; flex-direction: column; gap: 0.5rem; }
.user-card { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; text-decoration: none; color: inherit; border-radius: 6px; }
.user-card:hover { background: #2a2a4a; }
.avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.meta { display: block; font-size: 0.85rem; color: #999; }
</style>
