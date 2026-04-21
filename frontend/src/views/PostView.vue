<template>
  <!-- Fullscreen overlay — teleported outside the layout so nothing clips it -->
  <Teleport to="body">
    <div
      v-if="fullscreen"
      class="fullscreen-overlay"
      @wheel.prevent="fsOnWheel"
      @pointerdown="fsOnPointerDown"
      @pointermove="fsOnPointerMove"
      @pointerup="fsOnPointerUp"
      @pointercancel="fsOnPointerUp"
    >
      <video
        v-if="isVideo"
        :src="post?.file_url"
        class="fullscreen-img"
        :style="fsImgStyle"
        controls
        loop
        @click.stop
      />
      <img
        v-else
        :src="post?.file_url"
        class="fullscreen-img"
        :class="{ 'sfw-blurred': shouldBlur(post) }"
        :style="fsImgStyle"
        draggable="false"
      />
      <button class="fullscreen-close" @pointerdown.stop @pointerup.stop @click.stop="closeFullscreen" title="Close (Esc)">✕</button>
      <span v-if="fsScale > 1" class="fs-hint">Scroll to zoom · drag to pan · double-click to reset</span>
    </div>
  </Teleport>

  <div class="post-page">
    <div v-if="loading" class="text-muted load-msg">Loading…</div>

    <template v-else-if="post">
      <div class="post-layout">

        <!-- ── Left: image/video ── -->
        <div class="post-image-panel">
          <div class="post-image-wrapper">
            <video
              v-if="isVideo"
              :src="post.file_url"
              class="post-image post-video"
              :class="{ 'sfw-blurred': shouldBlur(post) }"
              controls
              loop
              preload="metadata"
            />
            <img
              v-else
              :src="post.file_url"
              :alt="post.title"
              class="post-image"
              :class="{ 'sfw-blurred': shouldBlur(post) }"
              @click="shouldBlur(post) ? reveal(post.id) : (fullscreen = true, fsResetZoom())"
              :title="shouldBlur(post) ? 'Click to reveal' : 'Click to view fullscreen'"
            />
            <div v-if="shouldBlur(post)" class="sfw-overlay post-sfw-overlay" @click="reveal(post.id)">Click to reveal</div>
          </div>
          <div class="image-meta">
            <span>{{ post.width }}×{{ post.height }}</span>
            <span>{{ formatFilesize(post.filesize) }}</span>
            <span>{{ post.file_type?.toUpperCase() }}</span>
          </div>
        </div>

        <!-- ── Right: info + tags ── -->
        <div class="post-info-panel">

          <!-- Info card -->
          <section class="info-card">
            <div class="info-grid">
              <span class="info-label">Rating</span>
              <span class="rating-badge" :class="`rating-${post.rating}`">{{ ratingLabel(post.rating) }}</span>

              <span class="info-label">ID</span>
              <span>#{{ post.id }}</span>

              <span class="info-label">Uploaded</span>
              <span>{{ formatDate(post.uploaded_at) }}</span>

              <template v-if="post.source">
                <span class="info-label">Source</span>
                <a :href="post.source" target="_blank" rel="noopener noreferrer" class="source-link" :title="post.source">
                  {{ sourceHostname }}
                </a>
              </template>

              <template v-if="post.imported_from && post.imported_from !== post.source">
                <span class="info-label">Origin</span>
                <a :href="post.imported_from" target="_blank" rel="noopener noreferrer" class="source-link">
                  {{ importedHostname }}
                </a>
              </template>

              <template v-if="artistTags.length">
                <span class="info-label">Artist</span>
                <span class="info-tag-row">
                  <router-link
                    v-for="t in artistTags" :key="t.name"
                    :to="{ name: 'posts', query: { tags: t.name } }"
                    class="tag tag-artist"
                  >{{ t.name }}</router-link>
                </span>
              </template>

              <template v-if="characterTags.length">
                <span class="info-label">Character</span>
                <span class="info-tag-row">
                  <router-link
                    v-for="t in characterTags" :key="t.name"
                    :to="{ name: 'posts', query: { tags: t.name } }"
                    class="tag tag-character"
                  >{{ t.name }}</router-link>
                </span>
              </template>

              <template v-if="copyrightTags.length">
                <span class="info-label">Copyright</span>
                <span class="info-tag-row">
                  <router-link
                    v-for="t in copyrightTags" :key="t.name"
                    :to="{ name: 'posts', query: { tags: t.name } }"
                    class="tag tag-copyright"
                  >{{ t.name }}</router-link>
                </span>
              </template>
            </div>

            <!-- Actions: vote + favourite + water -->
            <div class="actions-row actions-primary">
              <div class="vote-container">
                <button class="vote-btn" :class="{ voted: hasUpvoted }" @click="vote('upvote')">▲</button>
                <span class="score" :class="{ positive: post.score > 0, negative: post.score < 0 }">{{ post.score }}</span>
                <button class="vote-btn downvote" :class="{ voted: hasDownvoted }" @click="vote('downvote')">▼</button>
              </div>

              <button
                class="fav-btn"
                :class="{ favourited: hasFavourited }"
                @click="doFavourite"
                :title="hasFavourited ? 'Remove from favourites' : 'Add to favourites'"
              >
                {{ hasFavourited ? '♥' : '♡' }}
              </button>

              <button
                class="water-btn"
                :class="{ splash: waterSplash }"
                @click="doWater"
                title="Water this post"
              >
                💧 {{ waterCount }}
              </button>
            </div>

            <!-- Actions: collection + edit -->
            <div class="actions-row actions-secondary">
              <div v-if="auth.isAuthenticated" class="collection-picker-wrap" @focusout="handleCollectionBlur">
                <button class="btn-sm" @click="showCollectionPicker = !showCollectionPicker" title="Add to collection">
                  + Collection
                </button>
                <div v-if="showCollectionPicker" class="collection-dropdown">
                  <p v-if="!userCollections.length" class="coll-empty">No collections yet.</p>
                  <button
                    v-for="c in userCollections"
                    :key="c.id"
                    class="coll-option"
                    :disabled="addingToCollection"
                    @mousedown.prevent="addToCollection(c.id)"
                  >{{ c.title }}</button>
                  <router-link to="/collections" class="coll-new-link" @mousedown.prevent>New collection…</router-link>
                </div>
              </div>

              <button v-if="canEdit" class="btn-sm" @click="metaEditMode = !metaEditMode">
                {{ metaEditMode ? '✕ Cancel' : '✏ Edit' }}
              </button>
            </div>

            <!-- Meta edit form (rating / source / description) -->
            <form v-if="metaEditMode" @submit.prevent="saveMetaEdit" class="meta-edit-form">
              <div class="field">
                <label>Rating</label>
                <select v-model="editRating">
                  <option value="g">General</option>
                  <option value="q">Questionable</option>
                  <option value="s">Sensitive</option>
                  <option value="e">Explicit</option>
                </select>
              </div>
              <div class="field">
                <label>Source</label>
                <input v-model="editSource" placeholder="https://…" />
              </div>
              <div class="field">
                <label>Description</label>
                <textarea v-model="editDescription" rows="3"></textarea>
              </div>
              <div class="meta-edit-delete">
                <template v-if="!deleteConfirm">
                  <button type="button" class="btn-delete" @click="deleteConfirm = true">🗑 Delete post</button>
                </template>
                <template v-else>
                  <span class="delete-confirm-msg">Are you sure? This cannot be undone.</span>
                  <button type="button" class="btn-delete btn-delete-confirm" :disabled="deleting" @click="deletePost">{{ deleting ? 'Deleting…' : 'Yes, delete' }}</button>
                  <button type="button" class="btn-sm" @click="deleteConfirm = false">Cancel</button>
                </template>
              </div>
            </form>

            <!-- Description (view mode) -->
            <div v-if="!metaEditMode && post.description" class="description-block">
              <span class="info-label">Description</span>
              <p>{{ post.description }}</p>
            </div>
          </section>

          <!-- Tags panel -->
          <section class="tags-panel">
            <div class="tags-panel-header">
              <span>Tags</span>
              <span class="tag-count-badge">{{ post.tags.length }}</span>
            </div>

            <!-- Tag search (editors only) -->
            <div v-if="canEdit && metaEditMode" class="tag-search-wrapper" @focusout="handleTagSearchBlur">
              <input
                v-model="tagQuery"
                @input="onTagSearch"
                @keydown.escape="tagSuggestions = []"
                placeholder="Add a tag…"
                class="tag-search-input"
                autocomplete="off"
              />
              <div v-if="tagSuggestions.length" class="tag-suggestions">
                <button
                  v-for="s in tagSuggestions"
                  :key="s.name"
                  class="tag-suggestion"
                  :class="`tag-${s.type}`"
                  tabindex="0"
                  @mousedown.prevent="addTag(s)"
                >
                  <span class="sug-type">{{ s.type }}</span>{{ s.name }}
                </button>
              </div>
            </div>

            <div v-if="canEdit && metaEditMode" class="ai-tagging-panel">
              <div class="ai-tagging-header">
                <span class="tag-group-label">AI Suggestions</span>
                <div class="ai-tagging-actions">
                  <button class="btn-sm" :disabled="!deepdanbooruStatus.available || deepdanbooruLoading" @click="fetchDeepDanbooruSuggestions">
                    {{ deepdanbooruLoading ? 'Analyzing…' : 'Suggest tags' }}
                  </button>
                  <button v-if="availableAiSuggestions.length > 1" class="btn-sm" @click="addAllAiSuggestions">Add all</button>
                </div>
              </div>
              <p v-if="deepdanbooruError" class="text-error">{{ deepdanbooruError }}</p>
              <p v-else-if="!deepdanbooruStatus.loaded" class="text-muted">Checking DeepDanbooru availability…</p>
              <p v-else-if="!deepdanbooruStatus.available" class="text-muted">{{ deepdanbooruStatus.reason }}</p>
              <p v-else-if="!availableAiSuggestions.length && deepdanbooruSuggestions.length" class="text-muted">All suggested tags are already present.</p>
              <p v-else-if="!availableAiSuggestions.length" class="text-muted">Generate tag suggestions from this post’s media.</p>
              <div v-if="availableAiSuggestions.length" class="ai-suggestion-list">
                <button
                  v-for="suggestion in availableAiSuggestions"
                  :key="suggestion.tag"
                  class="ai-suggestion-chip"
                  :class="`tag-${suggestion.type}`"
                  @click="addAiSuggestion(suggestion)"
                >
                  <span>{{ suggestion.name }}</span>
                  <small>{{ formatScore(suggestion.score) }}</small>
                </button>
              </div>
            </div>

            <!-- Tags grouped by type -->
            <div v-for="(tags, type) in sortedTags" :key="type" class="tag-group">
              <div class="tag-group-label">{{ capitalize(type) }}</div>
              <div class="tag-chips">
                <span
                  v-for="tag in tags"
                  :key="tag.name"
                  class="tag-chip"
                  :class="`tag-${tag.type}`"
                >
                  <router-link :to="{ name: 'tag', params: { id: tag.id } }">{{ tag.name }}</router-link>
                  <button
                    v-if="canEdit && metaEditMode"
                    class="tag-remove-btn"
                    @click="removeTag(tag)"
                    title="Remove tag"
                  >×</button>
                </span>
              </div>
            </div>

            <!-- Save / cancel below tags (only in edit mode) -->
            <div v-if="canEdit && metaEditMode" class="tags-edit-actions">
              <button class="btn-primary" :disabled="saving" @click="saveMetaEdit">{{ saving ? 'Saving…' : 'Save' }}</button>
              <button class="btn-secondary" @click="metaEditMode = false">Cancel</button>
              <p v-if="metaEditError" class="text-error">{{ metaEditError }}</p>
            </div>
          </section>

        </div>
      </div>

      <!-- Comments -->
      <section class="comments-section">
        <h2>Comments</h2>
        <div v-if="auth.isAuthenticated" class="comment-compose">
          <textarea v-model="newComment" placeholder="Add a comment…" rows="2"></textarea>
          <button @click="addComment">Post</button>
        </div>
        <div class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <strong>{{ c.author?.username }}</strong>: {{ c.content }}
          </div>
          <p v-if="!comments.length" class="text-muted">No comments yet.</p>
        </div>
      </section>
    </template>

    <p v-else class="text-muted load-msg">Post not found.</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useSfwMode } from '@/composables/useSfwMode'
const props = defineProps({ id: [String, Number] })
const auth = useAuthStore()
const router = useRouter()
const { shouldBlur, reveal } = useSfwMode()

// ── Post data ──
const post = ref(null)
const comments = ref([])
const loading = ref(true)

// ── Votes / water ──
const hasUpvoted = ref(false)
const hasDownvoted = ref(false)
const hasFavourited = ref(false)
const waterCount = ref(0)
const waterSplash = ref(false)

// ── Fullscreen ──
const fullscreen = ref(false)
const fsScale = ref(1)
const fsPan = ref({ x: 0, y: 0 })

const _VIDEO_TYPES = new Set(['mp4', 'webm', 'mov', 'avi', 'mkv', 'm4v'])
const isVideo = computed(() => _VIDEO_TYPES.has(post.value?.file_type?.toLowerCase()))

const fsImgStyle = computed(() => ({
  transform: `translate(${fsPan.value.x}px, ${fsPan.value.y}px) scale(${fsScale.value})`,
  cursor: fsScale.value > 1 ? 'grab' : 'default',
  userSelect: 'none',
}))

function closeFullscreen() {
  fullscreen.value = false
  fsScale.value = 1
  fsPan.value = { x: 0, y: 0 }
  fsPointers.clear()
}

function fsResetZoom() {
  fsScale.value = 1
  fsPan.value = { x: 0, y: 0 }
}

function fsOnWheel(e) {
  const delta = e.deltaY < 0 ? 1.15 : 1 / 1.15
  fsScale.value = Math.min(10, Math.max(1, fsScale.value * delta))
  if (fsScale.value === 1) fsPan.value = { x: 0, y: 0 }
}

// ── Pointer tracking (mouse drag + pinch zoom) ──
const fsPointers = new Map()
let fsDragStart = null
let fsPinchDist = null

function fsPointerDist() {
  const pts = [...fsPointers.values()]
  const dx = pts[1].x - pts[0].x
  const dy = pts[1].y - pts[0].y
  return Math.hypot(dx, dy)
}

function fsOnPointerDown(e) {
  fsPointers.set(e.pointerId, { x: e.clientX, y: e.clientY })
  e.currentTarget.setPointerCapture(e.pointerId)
  if (fsPointers.size === 1) {
    fsDragStart = { x: e.clientX - fsPan.value.x, y: e.clientY - fsPan.value.y }
  }
  if (fsPointers.size === 2) {
    fsPinchDist = fsPointerDist()
    fsDragStart = null
  }
}

function fsOnPointerMove(e) {
  fsPointers.set(e.pointerId, { x: e.clientX, y: e.clientY })
  if (fsPointers.size === 2 && fsPinchDist !== null) {
    const newDist = fsPointerDist()
    const ratio = newDist / fsPinchDist
    fsScale.value = Math.min(10, Math.max(1, fsScale.value * ratio))
    fsPinchDist = newDist
    if (fsScale.value === 1) fsPan.value = { x: 0, y: 0 }
    return
  }
  if (fsPointers.size === 1 && fsDragStart && fsScale.value > 1) {
    fsPan.value = { x: e.clientX - fsDragStart.x, y: e.clientY - fsDragStart.y }
  }
}

function fsOnPointerUp(e) {
  fsPointers.delete(e.pointerId)
  if (fsPointers.size < 2) fsPinchDist = null
  if (fsPointers.size === 0) {
    // double-click to reset (two pointerup within 300ms with no move)
    if (e.detail === 2) fsResetZoom()
    // close only when not zoomed and it's a plain tap/click with no drag
    if (fsScale.value === 1 && fsDragStart) {
      const moved = Math.abs(e.clientX - (fsDragStart.x + fsPan.value.x)) < 4 &&
                    Math.abs(e.clientY - (fsDragStart.y + fsPan.value.y)) < 4
      if (moved) closeFullscreen()
    }
    fsDragStart = null
  }
}

// ── Meta editing (rating / source / description) ──
const metaEditMode = ref(false)
const saving = ref(false)
const metaEditError = ref('')
const editRating = ref('')
const editSource = ref('')
const editDescription = ref('')
const deleteConfirm = ref(false)
const deleting = ref(false)

// ── Tag editing ──
const tagQuery = ref('')
const tagSuggestions = ref([])
let tagSearchTimer = null
const deepdanbooruStatus = ref({ loaded: false, available: false, reason: '', threshold: 0.5 })
const deepdanbooruLoading = ref(false)
const deepdanbooruSuggestions = ref([])
const deepdanbooruError = ref('')

// ── Collection picker ──
const userCollections = ref([])
const showCollectionPicker = ref(false)
const addingToCollection = ref(false)

// ── Comments ──
const newComment = ref('')

// ── Computed ──
const canEdit = computed(() =>
  auth.isAuthenticated &&
  post.value &&
  (auth.user?.role >= 100 || auth.user?.id === post.value.uploader_id)
)

const TAG_ORDER = ['artist', 'circle', 'character', 'copyright', 'species', 'general', 'meta']

const sortedTags = computed(() => {
  if (!post.value?.tags) return {}
  const groups = {}
  for (const t of post.value.tags) {
    ;(groups[t.type] ??= []).push(t)
  }
  for (const type in groups) groups[type].sort((a, b) => a.name.localeCompare(b.name))
  const result = {}
  for (const type of TAG_ORDER) if (groups[type]) result[type] = groups[type]
  for (const type in groups) if (!result[type]) result[type] = groups[type]
  return result
})

const artistTags    = computed(() => post.value?.tags.filter(t => t.type === 'artist')    ?? [])
const characterTags = computed(() => post.value?.tags.filter(t => t.type === 'character') ?? [])
const copyrightTags = computed(() => post.value?.tags.filter(t => t.type === 'copyright') ?? [])
const availableAiSuggestions = computed(() => {
  if (!post.value?.tags) return deepdanbooruSuggestions.value
  const existing = new Set(post.value.tags.map(tagToStr))
  return deepdanbooruSuggestions.value.filter(item => !existing.has(item.tag))
})

const sourceHostname = computed(() => {
  try { return new URL(post.value?.source || '').hostname } catch { return post.value?.source || '' }
})
const importedHostname = computed(() => {
  try { return new URL(post.value?.imported_from || '').hostname } catch { return post.value?.imported_from || '' }
})

// ── Lifecycle ──
onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  try {
    const [postRes, commentRes] = await Promise.all([
      api.get('/post', { params: { id: props.id } }),
      api.get('/comments', { params: { post_id: props.id } }),
    ])
    post.value = postRes.data
    hasUpvoted.value   = postRes.data.has_upvoted    ?? false
    hasDownvoted.value = postRes.data.has_downvoted  ?? false
    hasFavourited.value = postRes.data.has_favourited ?? false
    waterCount.value   = postRes.data.water_count    ?? 0
    comments.value    = commentRes.data.data ?? []
  } finally {
    loading.value = false
  }
  // Pre-load collections for authenticated users
  if (auth.isAuthenticated) {
    try {
      const { data } = await api.get('/collections', { params: { per_page: 200, creator: auth.user?.id } })
      userCollections.value = data.data ?? []
    } catch { /* non-fatal */ }
  }
  fetchDeepDanbooruStatus()
})
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

function onKeydown(e) {
  if (e.key === 'Escape') closeFullscreen()
}

watch(metaEditMode, val => {
  if (val && post.value) {
    editRating.value = post.value.rating
    editSource.value = post.value.source || ''
    editDescription.value = post.value.description || ''
    metaEditError.value = ''
    deleteConfirm.value = false
  }
})

// ── Meta save ──
async function saveMetaEdit() {
  saving.value = true
  metaEditError.value = ''
  try {
    const { data } = await api.put('/post', {
      id: Number(props.id),
      rating: editRating.value,
      source: editSource.value,
      description: editDescription.value,
    })
    post.value = data
    metaEditMode.value = false
  } catch (err) {
    metaEditError.value = err.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}

async function deletePost() {
  deleting.value = true
  try {
    await api.delete('/post', { data: { id: Number(props.id) } })
    router.push('/posts')
  } catch (err) {
    metaEditError.value = err.response?.data?.message || 'Delete failed.'
    deleteConfirm.value = false
  } finally {
    deleting.value = false
  }
}

async function fetchDeepDanbooruStatus() {
  try {
    const { data } = await api.get('/posts/auto-tags/status')
    deepdanbooruStatus.value = {
      loaded: true,
      available: !!data.available,
      reason: data.reason || '',
      threshold: data.threshold ?? 0.5,
    }
  } catch {
    deepdanbooruStatus.value = {
      loaded: true,
      available: false,
      reason: 'Could not check DeepDanbooru availability.',
      threshold: 0.5,
    }
  }
}

// ── Tag helpers ──
function tagToStr(t) { return t.type !== 'general' ? `${t.type}:${t.name}` : t.name }
function tagsToStr(tags) { return tags.map(tagToStr).join(' ') }

async function updatePostTags(nextTags) {
  const oldStr = tagsToStr(post.value.tags)
  const newStr = nextTags.join(' ')
  const { data } = await api.put('/post', { id: Number(props.id), tags: newStr, old_tags: oldStr })
  post.value = data
  return data
}

async function addTag(suggestion) {
  const rawTag = suggestion.tag || tagToStr(suggestion)
  if (post.value.tags.some(t => tagToStr(t) === rawTag)) {
    tagQuery.value = ''
    tagSuggestions.value = []
    return
  }
  tagQuery.value = ''
  tagSuggestions.value = []
  try {
    await updatePostTags([...post.value.tags.map(tagToStr), rawTag])
  } catch (err) { console.error('Add tag failed:', err) }
}

async function removeTag(tag) {
  try {
    await updatePostTags(post.value.tags.filter(t => tagToStr(t) !== tagToStr(tag)).map(tagToStr))
  } catch (err) { console.error('Remove tag failed:', err) }
}

async function fetchDeepDanbooruSuggestions() {
  deepdanbooruLoading.value = true
  deepdanbooruError.value = ''
  try {
    const { data } = await api.post('/posts/auto-tags', { post_id: Number(props.id) })
    deepdanbooruSuggestions.value = data.data ?? []
  } catch (err) {
    deepdanbooruSuggestions.value = []
    deepdanbooruError.value = err.response?.data?.message || 'Could not generate AI tags.'
  } finally {
    deepdanbooruLoading.value = false
  }
}

function addAiSuggestion(suggestion) {
  addTag(suggestion)
}

async function addAllAiSuggestions() {
  if (!availableAiSuggestions.value.length) return
  try {
    const merged = new Set([
      ...post.value.tags.map(tagToStr),
      ...availableAiSuggestions.value.map(item => item.tag),
    ])
    await updatePostTags([...merged])
  } catch (err) {
    deepdanbooruError.value = err.response?.data?.message || 'Could not add AI tags.'
  }
}

function onTagSearch() {
  clearTimeout(tagSearchTimer)
  if (!tagQuery.value.trim()) { tagSuggestions.value = []; return }
  tagSearchTimer = setTimeout(async () => {
    try {
      const { data } = await api.get('/tags/autocomplete', { params: { query: tagQuery.value.trim() } })
      tagSuggestions.value = data.data ?? []
    } catch { tagSuggestions.value = [] }
  }, 200)
}

function handleTagSearchBlur(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) tagSuggestions.value = []
}

function handleCollectionBlur(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) showCollectionPicker.value = false
}

// ── Water / vote / comment ──
async function doWater() {
  waterCount.value++
  waterSplash.value = true
  setTimeout(() => { waterSplash.value = false }, 400)
  try {
    const { data } = await api.post('/posts/water', { post_id: Number(props.id) })
    waterCount.value = data.water_count
  } catch {
    waterCount.value--
  }
}

async function doFavourite() {
  const prev = hasFavourited.value
  hasFavourited.value = !prev
  try {
    const { data } = await api.post('/posts/favourite', { post_id: Number(props.id) })
    hasFavourited.value = data.has_favourited
  } catch {
    hasFavourited.value = prev
  }
}

async function vote(type) {
  const { data } = await api.post('/posts/vote', { post_id: Number(props.id), type })
  post.value.score = data.score
  hasUpvoted.value  = data.has_upvoted
  hasDownvoted.value = data.has_downvoted
}

async function addComment() {
  if (!newComment.value.trim()) return
  const { data } = await api.post('/comments', { post_id: Number(props.id), content: newComment.value })
  comments.value.unshift(data)
  newComment.value = ''
}

// ── Collection ──
async function addToCollection(collectionId) {
  addingToCollection.value = true
  try {
    await api.post('/collections/posts', {
      collection_id: collectionId,
      post_id: Number(props.id),
    })
    showCollectionPicker.value = false
  } catch (err) {
    console.error('Add to collection failed:', err)
  } finally {
    addingToCollection.value = false
  }
}

// ── Formatters ──
function ratingLabel(r) {
  return { g: 'General', q: 'Questionable', s: 'Sensitive', e: 'Explicit' }[r] ?? r?.toUpperCase() ?? ''
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function formatFilesize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(2)} MB`
}

function formatScore(score) {
  return Number(score).toFixed(2)
}

function capitalize(s) { return s ? s[0].toUpperCase() + s.slice(1) : '' }
</script>


<style scoped>
/* ── Page ── */
.post-page {
  max-width: 1500px;
  margin: 0 auto;
  padding: 1em 1.5em;
}
.load-msg { padding: 3em; text-align: center; }

/* ── Two-column layout ── */
.post-layout {
  display: flex;
  gap: 1.5em;
  align-items: flex-start;
}

/* ── Image panel ── */
.post-image-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6em;
}
.post-image-wrapper {
  position: relative;
  line-height: 0;
  border-radius: 8px;
}
.post-sfw-overlay {
  font-size: 1rem;
}
.post-image {
  max-width: 100%;
  max-height: 85vh;
  object-fit: contain;
  cursor: zoom-in;
  display: block;
  border-radius: 8px;
}
.post-video {
  cursor: default;
  width: 100%;
  background: #000;
}
.image-meta {
  display: flex;
  gap: 1em;
  font-size: 0.78rem;
  color: var(--text-dim);
}

/* ── Info panel ── */
.post-info-panel {
  width: 380px;
  min-width: 300px;
  max-width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 1em;
}

/* ── Info card ── */
.info-card {
  background: var(--bg-overlay);
  padding: 1em;
  display: flex;
  flex-direction: column;
  gap: 0.9em;
}
.info-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.45em 0.9em;
  align-items: start;
}
.info-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding-top: 0.15em;
  white-space: nowrap;
}
.info-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25em;
}
.source-link {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
  vertical-align: bottom;
}

/* ── Rating badges ── */
.rating-badge {
  display: inline-block;
  padding: 0.12em 0.5em;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 0.3em;
}
.rating-g { background: #2d5a2d; color: #8fdf8f; }
.rating-q { background: #5a4d2d; color: #dfcf8f; }
.rating-s { background: #3b4a5a; color: #8fcddf; }
.rating-e { background: #5a2d2d; color: #df8f8f; }

/* ── Actions row ── */
.actions-row {
  display: flex;
  align-items: center;
  gap: 0.6em;
}
.actions-secondary {
  margin-top: 0.3em;
}
.water-btn {
  display: flex;
  align-items: center;
  gap: 0.35em;
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  height: 2.2em;
  padding: 0 0.8em;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background 0.15s, color 0.15s;
}
.water-btn:hover { background: var(--item-hover); }
.water-btn.splash { animation: water-splash 0.4s ease; }
@keyframes water-splash {
  0%   { transform: scale(1); }
  30%  { transform: scale(1.25); filter: brightness(1.4); }
  100% { transform: scale(1); }
}
.fav-btn {
  display: flex;
  align-items: center;
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  height: 2.2em;
  padding: 0 0.7em;
  font-size: 1rem;
  line-height: 1;
  color: var(--text-muted);
  transition: color 0.15s, background 0.15s;
}
.fav-btn:hover { background: var(--item-hover); color: #f87171; }
.fav-btn.favourited { color: #f87171; }
.vote-container {
  display: flex;
  align-items: center;
  gap: 0.2em;
  background: var(--bg-raised);
  height: 2.2em;
  padding: 0 0.5em;
}
.vote-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0 0.4em;
  font-size: 0.9rem;
  color: var(--text-muted);
  transition: color 0.15s;
}
.vote-btn:hover { color: var(--text); }
.vote-btn.voted { color: #4ade80; }
.vote-btn.downvote.voted { color: #f87171; }
.score { min-width: 1.8em; text-align: center; font-size: 0.9rem; user-select: none; }
.score.positive { color: #4ade80; }
.score.negative { color: #f87171; }
.btn-sm {
  background: var(--bg-raised);
  border: none;
  cursor: pointer;
  height: 2.2em;
  padding: 0 0.8em;
  font-size: 0.82rem;
  color: var(--text-muted);
}
.btn-sm:hover { background: var(--item-hover); color: var(--text); }

/* ── Meta edit form ── */
.meta-edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.55em;
  padding-top: 0.6em;
  border-top: 1px solid var(--border);
  border-radius: 0;
}
.meta-edit-form .field { display: flex; flex-direction: column; gap: 0.2em; }
.meta-edit-form label { font-size: 0.78rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.04em; }
.meta-edit-form input,
.meta-edit-form select,
.meta-edit-form textarea { width: 100%; }
.meta-edit-delete {
  display: flex;
  align-items: center;
  gap: 0.5em;
  flex-wrap: wrap;
  padding-top: 0.5em;
  border-top: 1px solid var(--border);
  border-radius: 0;
  margin-top: 0.25em;
}
.delete-confirm-msg { font-size: 0.82rem; color: var(--text-muted); flex: 1; }
.btn-delete {
  background: transparent;
  border: 1px solid #7f3434;
  color: #f87171;
  cursor: pointer;
  padding: 0.3em 0.75em;
  font-size: 0.82rem;
  transition: background 0.15s;
}
.btn-delete:hover { background: #3d1a1a; }
.btn-delete-confirm { background: #5a1f1f; }
.btn-delete-confirm:hover { background: #7f2a2a; }

/* ── Description view ── */
.description-block {
  padding-top: 0.6em;
  border-top: 1px solid var(--border);
  border-radius: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3em;
}
.description-block p {
  white-space: pre-wrap;
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0;
}

/* ── Tags panel ── */
.tags-panel {
  background: var(--bg-overlay);
  padding: 1em;
  display: flex;
  flex-direction: column;
  gap: 0.8em;
}
.tags-panel-header {
  display: flex;
  align-items: center;
  gap: 0.5em;
  font-weight: 600;
  font-size: 0.95rem;
}
.tags-edit-actions {
  display: flex;
  align-items: center;
  gap: 0.5em;
  flex-wrap: wrap;
  margin-top: 0.25em;
}
.tag-count-badge {
  background: var(--bg-raised);
  color: var(--text-dim);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1em 0.5em;
  border-radius: 1em;
}

/* ── Tag search ── */
.tag-search-wrapper {
  position: relative;
}
.tag-search-input { width: 100%; font-size: 0.88rem; }
.tag-suggestions {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  z-index: 200;
  max-height: 220px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  border-radius: 0 0 0.4em 0.4em;
}
.tag-suggestion {
  display: flex;
  align-items: center;
  gap: 0.5em;
  padding: 0.4em 0.75em;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  font-size: 0.85rem;
  width: 100%;
}
.tag-suggestion:hover,
.tag-suggestion:focus { background: var(--item-hover); outline: none; }
.sug-type {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--text-dim);
  min-width: 4.5em;
  flex-shrink: 0;
}

.ai-tagging-panel {
  display: grid;
  gap: 0.55em;
}

.ai-tagging-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75em;
}

.ai-tagging-actions {
  display: flex;
  gap: 0.45em;
  flex-wrap: wrap;
}

.ai-suggestion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45em;
}

.ai-suggestion-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45em;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  padding: 0.32em 0.58em;
  font-size: 0.8rem;
}

.ai-suggestion-chip small {
  color: var(--text-muted);
}

/* ── Tag groups ── */
.tag-group { display: flex; flex-direction: column; gap: 0.3em; }
.tag-group-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--text-dim);
  font-weight: 700;
}
.tag-chips { display: flex; flex-wrap: wrap; gap: 0.3em; }
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.2em;
  padding: 0.15em 0.45em;
  font-size: 0.82rem;
  font-weight: 500;
  border-radius: 0.35em;
}
.tag-chip a { color: inherit; text-decoration: none; }
.tag-chip a:hover { text-decoration: underline; }
.tag-remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.45;
  padding: 0 0.05em;
  font-size: 1em;
  line-height: 1;
  flex-shrink: 0;
}
.tag-remove-btn:hover { opacity: 1; }

/* ── Comments ── */
.comments-section {
  margin-top: 1.5em;
  margin-left: auto;
  margin-right: auto;
  background: var(--bg-overlay);
  padding: 1.5em;
  max-width: 820px;
}
.comments-section h2 { margin-bottom: 1em; }
.comment-compose {
  display: flex;
  gap: 0.5em;
  margin-bottom: 1em;
  align-items: flex-start;
}
.comment-compose textarea { flex: 1; resize: vertical; min-height: 2.5em; }
.comment-list { display: flex; flex-direction: column; gap: 0.5em; }
.comment-item { padding: 0.3em 0; border-bottom: 1px solid var(--border); font-size: 0.9rem; }

/* ── Fullscreen overlay ── */
.fullscreen-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.92);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  touch-action: none;
}
.fullscreen-img {
  max-width: 96vw;
  max-height: 96vh;
  object-fit: contain;
  transform-origin: center center;
  transition: transform 0.05s ease;
  pointer-events: none;
}
.fs-hint {
  position: fixed;
  bottom: 1em;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,0.45);
  font-size: 0.78rem;
  pointer-events: none;
  white-space: nowrap;
}
.fullscreen-close {
  position: fixed;
  top: 0.8em;
  right: 0.8em;
  background: rgba(0, 0, 0, 0.65);
  border: none;
  color: #fff;
  font-size: 1.3rem;
  cursor: pointer;
  width: 2.2em;
  height: 2.2em;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  z-index: 1001;
}
.fullscreen-close:hover { background: rgba(255, 255, 255, 0.15); }

/* ── Responsive ── */
@media (max-width: 900px) {
  .post-layout { flex-direction: column; }
  .post-info-panel { width: 100%; min-width: 0; max-width: 100%; }
  .post-image { max-height: 65vh; }
  .comments-section { max-width: 100%; }
  .ai-tagging-header { align-items: flex-start; flex-direction: column; }
}

/* ── Collection picker ── */
.collection-picker-wrap {
  position: relative;
}
.collection-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 180px;
  background: var(--bg-raised);
  border: 1px solid var(--border-color, #444);
  border-radius: 6px;
  padding: 4px 0;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.coll-option {
  background: none;
  border: none;
  color: var(--text-color);
  padding: 7px 14px;
  text-align: left;
  cursor: pointer;
  font-size: 0.9rem;
  width: 100%;
}
.coll-option:hover { background: var(--item-hover); }
.coll-option:disabled { opacity: 0.5; cursor: not-allowed; }
.coll-empty {
  padding: 6px 14px;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0;
}
.coll-new-link {
  display: block;
  padding: 7px 14px;
  font-size: 0.85rem;
  color: var(--accent-color, #6ea0f0);
  border-top: 1px solid var(--border-color, #444);
  text-decoration: none;
}
.coll-new-link:hover { text-decoration: underline; }
</style>
