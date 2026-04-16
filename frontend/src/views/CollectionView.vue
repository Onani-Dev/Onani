<template>
  <div v-if="collection" class="page-container">
    <div class="col-header">
      <div>
        <h1>{{ collection.title }}</h1>
        <p class="text-muted">{{ collection.description }}</p>
      </div>
      <div v-if="canManage" class="header-actions">
        <button class="btn-icon" @click="editMode = !editMode">{{ editMode ? '✕' : '✏' }}</button>
        <button class="btn-icon danger" @click="deleteCollection">🗑</button>
      </div>
    </div>

    <!-- Edit title/description -->
    <form v-if="editMode" @submit.prevent="saveEdit" class="edit-panel">
      <div class="edit-field">
        <label>Title</label>
        <input v-model="editTitle" />
      </div>
      <div class="edit-field">
        <label>Description</label>
        <textarea v-model="editDesc" rows="3"></textarea>
      </div>
      <p v-if="editError" class="text-error">{{ editError }}</p>
      <div class="edit-buttons">
        <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button type="button" class="btn-secondary" @click="editMode = false">Cancel</button>
      </div>
    </form>

    <!-- Posts grid -->
    <div v-if="posts.length" class="post-grid">
      <div v-for="post in posts" :key="post.id" class="post-thumb-wrap">
        <router-link :to="`/posts/${post.id}`" class="post-thumb">
          <img :src="`/images/thumbnail/${post.filename}?size=large`" :alt="`Post #${post.id}`" loading="lazy" />
        </router-link>
        <button v-if="canManage" class="remove-btn" @click="removePost(post.id)" title="Remove from collection">✕</button>
      </div>
    </div>
    <p v-else class="text-muted">No posts in this collection.</p>

    <!-- Add posts (managers only) -->
    <div v-if="canManage" class="add-posts-section">
      <h3>Add Posts</h3>
      <div class="search-bar">
        <input v-model="searchQuery" placeholder="Search by tags..." @keyup.enter="searchPosts" />
        <button @click="searchPosts" :disabled="searching">{{ searching ? 'Searching...' : 'Search' }}</button>
      </div>
      <div v-if="searchResults.length" class="search-grid">
        <div v-for="post in searchResults" :key="post.id" class="post-thumb-wrap">
          <router-link :to="`/posts/${post.id}`" target="_blank" class="post-thumb">
            <img :src="`/images/thumbnail/${post.filename}?size=large`" :alt="`Post #${post.id}`" loading="lazy" />
          </router-link>
          <button
            class="add-btn"
            @click="addPost(post.id)"
            :disabled="posts.some(p => p.id === post.id)"
          >{{ posts.some(p => p.id === post.id) ? '✓' : '＋' }}</button>
        </div>
      </div>
    </div>
  </div>
  <p v-else-if="loading">Loading...</p>
  <p v-else>Collection not found.</p>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ id: [String, Number] })
const auth = useAuthStore()
const router = useRouter()

const collection = ref(null)
const posts = ref([])
const loading = ref(true)

const editMode = ref(false)
const editTitle = ref('')
const editDesc = ref('')
const editError = ref('')
const saving = ref(false)

const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)

const canManage = computed(() =>
  auth.user?.role >= 200 || auth.user?.id === collection.value?.creator
)

onMounted(async () => {
  try {
    const { data } = await api.get('/collections', { params: { id: props.id } })
    collection.value = data
    posts.value = data.posts || []
    editTitle.value = data.title
    editDesc.value = data.description
  } finally {
    loading.value = false
  }
})

async function saveEdit() {
  saving.value = true
  editError.value = ''
  try {
    const { data } = await api.put('/collections', {
      id: Number(props.id),
      title: editTitle.value,
      description: editDesc.value,
    })
    collection.value = { ...collection.value, ...data }
    editMode.value = false
  } catch (err) {
    editError.value = err.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}

async function deleteCollection() {
  if (!confirm('Delete this collection?')) return
  await api.delete('/collections', { data: { id: Number(props.id) } })
  router.push('/collections')
}

async function removePost(postId) {
  const { data } = await api.delete('/collections/posts', {
    data: { collection_id: Number(props.id), post_id: postId },
  })
  posts.value = data.posts || []
}

async function searchPosts() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    const { data } = await api.get('/posts', { params: { tags: searchQuery.value, per_page: 20 } })
    searchResults.value = data.data
  } finally {
    searching.value = false
  }
}

async function addPost(postId) {
  const { data } = await api.post('/collections/posts', {
    collection_id: Number(props.id),
    post_id: postId,
  })
  posts.value = data.posts || []
}
</script>

<style scoped>
.col-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1em;
}
.header-actions { display: flex; gap: 0.5em; flex-shrink: 0; }

.btn-icon {
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  padding: 4px 10px;
  font-size: 0.95rem;
  border-radius: 4px;
}
.btn-icon:hover { background: var(--item-hover); }
.btn-icon.danger:hover { background: #5a2d2d; }

.edit-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75em;
  background: var(--bg-raised);
  padding: 1em;
  margin-bottom: 1.5em;
  max-width: 500px;
}
.edit-field { display: flex; flex-direction: column; gap: 0.25em; }
.edit-field label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); }
.edit-field input, .edit-field textarea { width: 100%; }
.edit-buttons { display: flex; gap: 0.5em; }

.post-thumb-wrap {
  position: relative;
  display: inline-block;
}
.remove-btn, .add-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0,0,0,0.7);
  border: none;
  color: #fff;
  cursor: pointer;
  padding: 2px 6px;
  font-size: 0.8rem;
  border-radius: 3px;
  line-height: 1.4;
}
.remove-btn:hover { background: #5a2d2d; }
.add-btn:hover { background: #2d5a2d; }
.add-btn:disabled { opacity: 0.5; cursor: default; }

.add-posts-section {
  margin-top: 2em;
  padding-top: 1em;
  border-top: 1px solid var(--border);
}
.add-posts-section h3 { margin-bottom: 0.75em; }
.search-bar { display: flex; gap: 0.5em; margin-bottom: 1em; }
.search-bar input { flex: 1; }
.search-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(10em, 1fr));
  gap: 0.5em;
}
</style>
