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

    <div v-if="tag.posts?.length" class="post-grid">
      <router-link v-for="post in tag.posts" :key="post.id" :to="`/posts/${post.id}`" class="post-thumb">
        <img :src="`/images/thumbnail/${post.filename}?size=large`" :alt="`Post #${post.id}`" loading="lazy" />
      </router-link>
    </div>
  </div>
  <p v-else>Loading...</p>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ id: [String, Number] })
const auth = useAuthStore()
const tag = ref(null)
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

