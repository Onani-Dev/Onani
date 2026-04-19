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
          <div class="thumb-stack">
            <template v-if="c.preview_thumbnails && c.preview_thumbnails.length">
              <img
                v-for="(thumb, i) in c.preview_thumbnails.slice().reverse()"
                :key="i"
                :src="thumb.url"
                :class="[
                  'thumb-layer',
                  `thumb-layer-${c.preview_thumbnails.length - 1 - i}`,
                  { 'thumb-sfw-blur': shouldBlur(thumb) }
                ]"
                alt=""
                draggable="false"
              />
            </template>
            <div v-else class="thumb-empty">
              <span>&#128247;</span>
            </div>
          </div>
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

    <Pagination
      :page="page"
      :nextPage="nextPage"
      :prevPage="prevPage"
      v-model:perPage="perPage"
      :perPageOptions="[20, 40, 80]"
      @navigate="goToPage"
    />

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
import { ref, onMounted, watch } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useSfwMode } from '@/composables/useSfwMode'
import Pagination from '@/components/Pagination.vue'

const auth = useAuthStore()
const { shouldBlur } = useSfwMode()
const collections = ref([])
const page = ref(1)
const nextPage = ref(null)
const prevPage = ref(null)
const perPage = ref(40)
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
watch(perPage, () => { page.value = 1; fetchCollections() })

async function fetchCollections() {
  const { data } = await api.get('/collections', { params: { page: page.value, per_page: perPage.value } })
  collections.value = data.data
  nextPage.value = data.next_page
  prevPage.value = data.prev_page
}

function goToPage(p) {
  page.value = p
  fetchCollections()
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
    await api.post('/collections', {
      title: createTitle.value,
      description: createDescription.value,
    })
    createTitle.value = ''
    createDescription.value = ''
    showCreate.value = false
    page.value = 1
    await fetchCollections()
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
    openMenu.value = null
    await fetchCollections()
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
  display: flex;
  flex-direction: column;
  align-items: center;
}
.card-link:hover { background: var(--item-hover); }
.card-link h3 { margin: 0.75em 0 0.3em; text-align: center; width: 100%; }
.card-desc { font-size: 0.85rem; margin: 0; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; width: 100%; text-align: center; }

/* ── Thumbnail stack ─────────────────────────── */
.thumb-stack {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0.25em auto 0;
  flex-shrink: 0;
}
.thumb-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 3px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.45);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}
.thumb-sfw-blur { filter: blur(12px); }
/* each layer is slightly rotated so they fan out like scattered papers */
.thumb-layer-0 { transform: rotate(-6deg) translate(-3px, 3px);  z-index: 1; }
.thumb-layer-1 { transform: rotate(-2deg) translate(-1px, 1px); z-index: 2; }
.thumb-layer-2 { transform: rotate( 2deg) translate( 1px, 1px); z-index: 3; }
.thumb-layer-3 { transform: rotate( 0deg);                        z-index: 4; }
.card-link:hover .thumb-layer-0 { transform: rotate(-9deg)  translate(-7px, 5px); }
.card-link:hover .thumb-layer-1 { transform: rotate(-3deg)  translate(-3px, 2px); }
.card-link:hover .thumb-layer-2 { transform: rotate( 3deg)  translate( 3px, 2px); }
.card-link:hover .thumb-layer-3 { transform: rotate( 0deg)  translate(  0,  0);  box-shadow: 0 4px 16px rgba(0,0,0,0.6); }

.thumb-empty {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  border-radius: 3px;
  font-size: 2.5rem;
  color: var(--text-muted);
}

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

