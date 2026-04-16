<template>
  <div class="page-container">
    <div class="collections-header">
      <h1>Collections</h1>
      <button class="btn-icon" @click="showCreate = !showCreate" title="New collection">＋</button>
    </div>

    <!-- Create form -->
    <form v-if="showCreate" @submit.prevent="createCollection" class="create-form">
      <input v-model="createTitle" placeholder="Collection title" required />
      <textarea v-model="createDescription" placeholder="Description (optional)" rows="2"></textarea>
      <p v-if="createError" class="text-error">{{ createError }}</p>
      <div class="form-buttons">
        <button type="submit" :disabled="creating">{{ creating ? 'Creating...' : 'Create' }}</button>
        <button type="button" class="btn-secondary" @click="showCreate = false">Cancel</button>
      </div>
    </form>

    <div v-if="collections.length" class="collections-grid">
      <div v-for="c in collections" :key="c.id" class="collection-card">
        <router-link :to="`/collections/${c.id}`" class="card-link">
          <h3>{{ c.title }}</h3>
          <p class="card-desc text-muted">{{ c.description }}</p>
        </router-link>
        <div v-if="canManage(c)" class="card-actions">
          <button class="btn-icon" @click="toggleMenu(c.id)" title="Options">⚙</button>
          <div v-if="openMenu === c.id" class="card-dropdown">
            <button @click="startEdit(c)">Edit</button>
            <button class="danger" @click="deleteCollection(c.id)">Delete</button>
          </div>
        </div>
      </div>
    </div>
    <p v-else class="text-muted">No collections yet.</p>

    <!-- Edit modal -->
    <div v-if="editingCollection" class="modal-overlay" @click.self="editingCollection = null">
      <div class="modal">
        <h2>Edit Collection</h2>
        <form @submit.prevent="saveEdit" class="create-form">
          <input v-model="editTitle" placeholder="Title" required />
          <textarea v-model="editDescription" placeholder="Description" rows="3"></textarea>
          <p v-if="editError" class="text-error">{{ editError }}</p>
          <div class="form-buttons">
            <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
            <button type="button" class="btn-secondary" @click="editingCollection = null">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const collections = ref([])
const showCreate = ref(false)
const createTitle = ref('')
const createDescription = ref('')
const createError = ref('')
const creating = ref(false)
const openMenu = ref(null)
const editingCollection = ref(null)
const editTitle = ref('')
const editDescription = ref('')
const editError = ref('')
const saving = ref(false)

onMounted(fetchCollections)

async function fetchCollections() {
  const { data } = await api.get('/collections')
  collections.value = data.data
}

function canManage(c) {
  return auth.user?.role >= 200 || auth.user?.id === c.creator
}

function toggleMenu(id) {
  openMenu.value = openMenu.value === id ? null : id
}

async function createCollection() {
  creating.value = true
  createError.value = ''
  try {
    const { data } = await api.post('/collections', {
      title: createTitle.value,
      description: createDescription.value,
    })
    collections.value.unshift(data)
    createTitle.value = ''
    createDescription.value = ''
    showCreate.value = false
  } catch (err) {
    createError.value = err.response?.data?.message || 'Creation failed.'
  } finally {
    creating.value = false
  }
}

function startEdit(c) {
  editingCollection.value = c
  editTitle.value = c.title
  editDescription.value = c.description
  openMenu.value = null
}

async function saveEdit() {
  saving.value = true
  editError.value = ''
  try {
    const { data } = await api.put('/collections', {
      id: editingCollection.value.id,
      title: editTitle.value,
      description: editDescription.value,
    })
    const idx = collections.value.findIndex(c => c.id === data.id)
    if (idx !== -1) collections.value[idx] = data
    editingCollection.value = null
  } catch (err) {
    editError.value = err.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}

async function deleteCollection(id) {
  if (!confirm('Delete this collection?')) return
  try {
    await api.delete('/collections', { data: { id } })
    collections.value = collections.value.filter(c => c.id !== id)
    openMenu.value = null
  } catch {
    // ignore
  }
}
</script>

<style scoped>
.collections-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1em;
}
.btn-icon {
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  padding: 4px 10px;
  font-size: 1rem;
  border-radius: 4px;
}
.btn-icon:hover { background: var(--item-hover); }

.create-form {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
  background: var(--bg-raised);
  padding: 1em;
  margin-bottom: 1.5em;
  max-width: 500px;
}
.form-buttons { display: flex; gap: 0.5em; }

.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}
.collection-card {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  position: relative;
  display: flex;
  flex-direction: column;
}
.card-link {
  padding: 1rem;
  text-decoration: none;
  color: inherit;
  flex: 1;
}
.card-link:hover { background: var(--item-hover); }
.card-link h3 { margin: 0 0 0.4em; }
.card-desc { font-size: 0.85rem; margin: 0; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }

.card-actions {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
}
.card-dropdown {
  position: absolute;
  right: 0;
  top: 100%;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  min-width: 8em;
  z-index: 10;
  display: flex;
  flex-direction: column;
}
.card-dropdown button {
  background: none;
  border: none;
  padding: 0.5em 1em;
  text-align: left;
  cursor: pointer;
  color: var(--text);
  font-size: 0.9rem;
  border-radius: 0;
}
.card-dropdown button:hover { background: var(--item-hover); }
.card-dropdown button.danger { color: #df8f8f; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: var(--bg-raised);
  padding: 1.5em;
  min-width: 350px;
  max-width: 90vw;
}
.modal h2 { margin-bottom: 1em; }
</style>

