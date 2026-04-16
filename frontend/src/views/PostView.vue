<template>
  <div v-if="post">
    <div class="file-container">
      <img :src="post.file_url" :alt="`Post #${post.id}`" class="main-image" />
    </div>

    <div class="post-info-box">
      <div class="post-info-header">
        <div class="post-meta">
          <span class="rating-badge" :class="`rating-${post.rating}`">{{ post.rating?.toUpperCase() }}</span>
          <span v-if="post.source" class="post-source"><a :href="post.source" target="_blank" rel="noopener">source</a></span>
        </div>
        <div class="post-actions">
          <div v-if="auth.isAuthenticated" class="voting-container">
            <span class="vote-btn" @click="vote('upvote')" :class="{ voted: hasUpvoted }">▲</span>
            <span class="post-score-count" :class="{ positive: post.score > 0, negative: post.score < 0 }">{{ post.score }}</span>
            <span class="vote-btn" @click="vote('downvote')" :class="{ voted: hasDownvoted }">▼</span>
          </div>
          <button v-if="canEdit" class="btn-icon" @click="editMode = !editMode" :title="editMode ? 'Cancel' : 'Edit post'">
            {{ editMode ? '✕' : '✏' }}
          </button>
        </div>
      </div>

      <!-- Edit panel -->
      <form v-if="editMode" @submit.prevent="saveEdit" class="edit-panel">
        <div class="edit-field">
          <label>Tags</label>
          <textarea v-model="editTags" rows="3" placeholder="tag1 artist:name character:name"></textarea>
        </div>
        <div class="edit-row">
          <div class="edit-field">
            <label>Rating</label>
            <select v-model="editRating">
              <option value="g">General</option>
              <option value="q">Questionable</option>
              <option value="s">Sensitive</option>
              <option value="e">Explicit</option>
            </select>
          </div>
          <div class="edit-field">
            <label>Source</label>
            <input v-model="editSource" placeholder="https://..." />
          </div>
        </div>
        <div class="edit-field">
          <label>Description</label>
          <textarea v-model="editDescription" rows="3"></textarea>
        </div>
        <p v-if="editError" class="text-error">{{ editError }}</p>
        <div class="edit-buttons">
          <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
          <button type="button" class="btn-secondary" @click="editMode = false">Cancel</button>
        </div>
      </form>

      <div v-else class="post-info-body">
        <div v-if="post.description" class="description-container">
          <h3>Description</h3>
          <p>{{ post.description }}</p>
        </div>
        <div class="tags-section">
          <h3>Tags</h3>
          <div class="tags-list">
            <router-link
              v-for="tag in post.tags"
              :key="tag.name"
              :to="`/tags?q=${tag.name}`"
              class="tag"
              :class="`tag-${tag.type}`"
            >{{ tag.name }}</router-link>
          </div>
        </div>
      </div>
    </div>

    <div class="post-comments-box">
      <h2>Comments</h2>
      <div v-if="auth.isAuthenticated" class="comment-input-container">
        <textarea v-model="newComment" placeholder="Add a comment..." rows="2" class="comment-input"></textarea>
        <button @click="addComment" class="comment-submit">Post</button>
      </div>
      <div class="comment-container">
        <div v-for="c in comments" :key="c.id" class="comment">
          <strong>{{ c.author?.username }}</strong>: {{ c.content }}
        </div>
        <p v-if="!comments.length" class="text-muted">No comments yet.</p>
      </div>
    </div>
  </div>
  <p v-else-if="loading">Loading...</p>
  <p v-else>Post not found.</p>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ id: [String, Number] })
const auth = useAuthStore()

const post = ref(null)
const comments = ref([])
const loading = ref(true)
const newComment = ref('')
const hasUpvoted = ref(false)
const hasDownvoted = ref(false)

const editMode = ref(false)
const saving = ref(false)
const editError = ref('')
const editTags = ref('')
const editRating = ref('')
const editSource = ref('')
const editDescription = ref('')

const canEdit = computed(() =>
  auth.isAuthenticated &&
  post.value &&
  (auth.user?.role >= 100 || auth.user?.id === post.value.uploader_id)
)

onMounted(async () => {
  try {
    const { data } = await api.get('/post', { params: { id: props.id } })
    post.value = data
    const commentRes = await api.get('/comments', { params: { post_id: props.id } })
    comments.value = commentRes.data.data
  } finally {
    loading.value = false
  }
})

function openEdit() {
  if (!post.value) return
  editTags.value = post.value.tags
    .map(t => t.type !== 'general' ? `${t.type}:${t.name}` : t.name)
    .join(' ')
  editRating.value = post.value.rating
  editSource.value = post.value.source || ''
  editDescription.value = post.value.description || ''
  editMode.value = true
}

watch(() => editMode.value, (val) => { if (val) openEdit() })

async function saveEdit() {
  saving.value = true
  editError.value = ''
  const oldTags = post.value.tags
    .map(t => t.type !== 'general' ? `${t.type}:${t.name}` : t.name)
    .join(' ')
  try {
    const { data } = await api.put('/post', {
      id: Number(props.id),
      tags: editTags.value,
      old_tags: oldTags,
      rating: editRating.value,
      source: editSource.value,
      description: editDescription.value,
    })
    post.value = data
    editMode.value = false
  } catch (err) {
    editError.value = err.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}

async function vote(type) {
  const { data } = await api.post('/posts/vote', { post_id: Number(props.id), type })
  post.value.score = data.score
  hasUpvoted.value = data.has_upvoted
  hasDownvoted.value = data.has_downvoted
}

async function addComment() {
  if (!newComment.value.trim()) return
  const { data } = await api.post('/comments', { post_id: Number(props.id), content: newComment.value })
  comments.value.unshift(data)
  newComment.value = ''
}
</script>


<style scoped>
.file-container {
  display: flex;
  justify-content: center;
  padding: 1em;
}
.main-image {
  max-width: 100%;
  object-fit: scale-down;
}

.post-info-box {
  background-color: var(--bg-overlay);
  margin: 0 auto 1em;
  padding: 1em;
  width: 60vw;
  overflow-wrap: anywhere;
}
.post-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75em;
}
.post-meta {
  display: flex;
  align-items: center;
  gap: 0.75em;
  font-size: 0.85rem;
}
.post-source a { color: var(--link); }
.post-actions {
  display: flex;
  align-items: center;
  gap: 0.5em;
}
.voting-container {
  display: flex;
  align-items: center;
  gap: 0.3em;
  background-color: var(--bg-raised);
  padding: 4px 8px;
}
.vote-btn {
  cursor: pointer;
  user-select: none;
  padding: 0 0.4em;
  font-size: 0.9rem;
}
.vote-btn.voted { color: lightgreen; }
.vote-btn.voted:last-child { color: crimson; }
.post-score-count {
  font-size: 0.95rem;
  min-width: 1.5em;
  text-align: center;
  user-select: none;
}
.post-score-count.positive { color: lightgreen; }
.post-score-count.negative { color: crimson; }

.btn-icon {
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 0.95rem;
  border-radius: 4px;
}
.btn-icon:hover { background: var(--item-hover); }

.rating-badge {
  padding: 0.15em 0.5em;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 700;
}
.rating-g { background: #2d5a2d; color: #8fdf8f; }
.rating-q { background: #5a4d2d; color: #dfcf8f; }
.rating-s { background: #3b4a5a; color: #8fcddf; }
.rating-e { background: #5a2d2d; color: #df8f8f; }

.post-info-body { display: flex; flex-direction: column; gap: 1em; }
.description-container {
  background-color: var(--bg-raised);
  padding: 1em;
}
.description-container p { white-space: pre-wrap; margin: 0; }
.tags-section { }
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.5rem;
}
.tags-list a { text-decoration: none; }

/* Edit panel */
.edit-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75em;
  background: var(--bg-raised);
  padding: 1em;
}
.edit-field { display: flex; flex-direction: column; gap: 0.25em; }
.edit-field label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); }
.edit-field textarea, .edit-field input, .edit-field select { width: 100%; }
.edit-row { display: flex; gap: 1em; }
.edit-row .edit-field { flex: 1; }
.edit-buttons { display: flex; gap: 0.5em; }

.post-comments-box {
  margin: 0 auto 2em;
  padding: 1.5em;
  width: 50vw;
  background-color: var(--bg-overlay);
}
.post-comments-box h2 { margin-bottom: 1em; }
.comment-input-container {
  display: flex;
  gap: 0.5em;
  margin-bottom: 1em;
  align-items: flex-start;
}
.comment-input {
  flex: 1;
  min-height: 2.5em;
  max-height: 8em;
  resize: vertical;
}
.comment-container { display: flex; flex-direction: column; gap: 0.5em; }
.comment { padding: 0.25em 0; border-bottom: 1px solid var(--border); }

@media (max-width: 689px) {
  .post-info-box { width: 92vw; }
  .post-comments-box { width: 92vw; padding: 0.8em; }
  .edit-row { flex-direction: column; }
}
@media (min-width: 690px) and (max-width: 1110px) {
  .post-info-box { width: 80vw; }
  .post-comments-box { width: 70vw; }
}
</style>

