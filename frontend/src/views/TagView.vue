<template>
  <div v-if="tag" class="page-container">
    <div class="tag-header">
      <div>
        <h1>{{ tag.name }}</h1>
        <p class="text-muted">{{ tag.type }} · {{ tag.post_count }} posts</p>
      </div>
      <button v-if="canEdit" class="btn-icon" @click="editMode = !editMode">{{ editMode ? '✕' : '✏' }}</button>
    </div>

    <form v-if="editMode" @submit.prevent="saveTag" class="edit-panel">
      <div class="edit-row">
        <div class="edit-field">
          <label>Name</label>
          <input v-model="editName" />
        </div>
        <div class="edit-field">
          <label>Type</label>
          <select v-model="editType">
            <option value="general">General</option>
            <option value="artist">Artist</option>
            <option value="character">Character</option>
            <option value="copyright">Copyright</option>
            <option value="meta">Meta</option>
            <option value="banned">Banned</option>
          </select>
        </div>
      </div>
      <p v-if="editError" class="text-error">{{ editError }}</p>
      <div class="edit-buttons">
        <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button type="button" class="btn-secondary" @click="editMode = false">Cancel</button>
      </div>
    </form>

    <div v-if="posts.length" class="post-grid">
      <PostThumb v-for="post in posts" :key="post.id" :post="post" />
    </div>
    <p v-else-if="!loading">No posts found.</p>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" :per-page="perPage" :total-pages="totalPages" @navigate="goToPage" @update:perPage="onPerPage" />
  </div>
  <p v-else>Loading...</p>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import Pagination from '@/components/Pagination.vue'
import PostThumb from '@/components/PostThumb.vue'

const props = defineProps({ id: [String, Number] })
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const tag = ref(null)
const posts = ref([])
const loading = ref(true)
const page = ref(Number(route.query.page) || 1)
const perPage = ref(Number(route.query.per_page) || 30)
const nextPage = ref(null)
const prevPage = ref(null)
const total = ref(0)
const totalPages = computed(() => total.value && perPage.value ? Math.ceil(total.value / perPage.value) : null)
const editMode = ref(false)
const editName = ref('')
const editType = ref('')
const saving = ref(false)
const editError = ref('')

const canEdit = computed(() => auth.user?.role >= 200)

onMounted(async () => {
  const { data } = await api.get('/tags', { params: { id: props.id } })
  tag.value = data
  editName.value = data.name
  editType.value = data.type
  await fetchPosts()
})

async function fetchPosts() {
  loading.value = true
  try {
    const { data } = await api.get('/posts', { params: { page: page.value, per_page: perPage.value, tags: tag.value.name } })
    posts.value = data.data
    nextPage.value = data.next_page
    prevPage.value = data.prev_page
    total.value = data.total ?? 0
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  page.value = p
  router.push({ query: { ...route.query, page: p > 1 ? p : undefined } })
  fetchPosts()
}

function onPerPage(n) {
  perPage.value = n
  page.value = 1
  router.push({ query: { ...route.query, page: undefined, per_page: n !== 30 ? n : undefined } })
  fetchPosts()
}

watch(() => [route.query.page, route.query.per_page], ([newPage, newPerPage]) => {
  page.value = Number(newPage) || 1
  perPage.value = Number(newPerPage) || 30
  if (tag.value) fetchPosts()
})

async function saveTag() {
  saving.value = true
  editError.value = ''
  try {
    const { data } = await api.put('/tags', { id: Number(props.id), name: editName.value, type: editType.value })
    tag.value = { ...tag.value, name: data.name, type: data.type }
    editMode.value = false
  } catch (err) {
    editError.value = err.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.tag-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1em;
}
.btn-icon {
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  padding: 4px 10px;
  font-size: 0.95rem;
  border-radius: 4px;
  flex-shrink: 0;
}
.btn-icon:hover { background: var(--item-hover); }
.edit-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75em;
  background: var(--bg-raised);
  padding: 1em;
  margin-bottom: 1em;
  max-width: 500px;
}
.edit-field { display: flex; flex-direction: column; gap: 0.25em; }
.edit-field label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); }
.edit-field input, .edit-field select { width: 100%; }
.edit-row { display: flex; gap: 1em; }
.edit-row .edit-field { flex: 1; }
.edit-buttons { display: flex; gap: 0.5em; }
</style>

