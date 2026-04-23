<template>
  <div class="upload-page page-container">
    <div class="upload-layout">
      <aside class="upload-sidebar">
        <h1>Upload</h1>
        <p class="text-muted">Drop an image or video, add tags, then publish in one pass.</p>
        <div class="tips-card">
          <h3>Quick Tips</h3>
          <ul>
            <li>Use clear, searchable tags.</li>
            <li>Set rating correctly before posting.</li>
            <li>Add source URL whenever possible.</li>
          </ul>
        </div>
      </aside>

      <form class="upload-content" @submit.prevent="handleUpload">
        <section class="section-card">
          <div class="section-head">
            <h2>Media</h2>
            <button type="button" class="btn-secondary btn-sm" @click="openFilePicker">Choose File</button>
          </div>

          <input
            ref="fileInput"
            class="native-file-input"
            type="file"
            accept="image/*,video/*"
            @change="onNativeFileChange"
          />

          <div
            class="drop-zone"
            :class="{ active: dragActive }"
            @click="openFilePicker"
            @dragenter.prevent="dragActive = true"
            @dragover.prevent="dragActive = true"
            @dragleave.prevent="dragActive = false"
            @drop.prevent="onDrop"
          >
            <template v-if="previewUrl">
              <img v-if="!isVideo" :src="previewUrl" alt="Upload preview" class="media-preview" />
              <video v-else :src="previewUrl" class="media-preview" controls muted playsinline />
            </template>
            <div v-else class="drop-placeholder">
              <strong>Drop file here</strong>
              <span class="text-muted">or click to browse</span>
            </div>
          </div>

          <div v-if="file" class="file-meta-row">
            <span class="status-badge status-pending">{{ isVideo ? 'Video' : 'Image' }}</span>
            <span class="text-muted">{{ file.name }}</span>
            <span class="text-muted">{{ formatBytes(file.size) }}</span>
            <button type="button" class="btn-danger btn-sm" @click="clearFile">Remove</button>
          </div>
        </section>

        <section class="section-card">
          <h2>Metadata</h2>

          <div class="field">
            <label>Tags</label>
            <div class="tag-input-wrap" @click="focusTagInput">
              <div class="tag-editor">
                <span v-for="tag in tags" :key="tag" class="tag-chip">
                  {{ tag }}
                  <button type="button" class="tag-remove" @click.stop="removeTag(tag)">×</button>
                </span>
                <input
                  ref="tagInput"
                  v-model="tagDraft"
                  placeholder="Add tag and press Enter"
                  autocomplete="off"
                  @keydown="onTagKeydown"
                  @keydown.backspace="backspaceTag"
                  @input="onTagInput"
                  @blur="hideSuggestionsDelayed"
                />
              </div>
              <ul v-if="tagSuggestions.length" class="autocomplete-list">
                <li
                  v-for="(tag, index) in tagSuggestions"
                  :key="tag.id"
                  class="autocomplete-item"
                  :class="[{ active: index === tagSuggestionIndex }, `tag-${(tag.type || '').toLowerCase()}`]"
                  @mousedown.prevent="applySuggestion(tag.name)"
                >
                  <span class="ac-name">{{ tag.name }}</span>
                  <span class="ac-count">{{ tag.post_count }}</span>
                </li>
              </ul>
              <div v-if="newTagActions.length" class="new-tag-actions">
                <button
                  v-for="action in newTagActions"
                  :key="action.value"
                  type="button"
                  class="new-tag-btn"
                  :class="`tag-${action.className}`"
                  @mousedown.prevent="applyNewTypedTag(action)"
                >
                  + New {{ action.label }} tag
                </button>
              </div>
            </div>
            <p class="field-hint">Space-separated tags are supported when pasting.</p>
          </div>

          <div class="field deepdanbooru-field">
            <div class="field-label-row">
              <label>AI Tag Suggestions</label>
              <div class="deepdanbooru-actions">
                <button
                  type="button"
                  class="btn-secondary btn-sm"
                  :disabled="!canSuggestWithDeepDanbooru || deepdanbooruLoading"
                  @click="suggestTagsWithDeepDanbooru"
                >{{ deepdanbooruLoading ? 'Analyzing…' : 'Suggest Tags' }}</button>
                <button
                  v-if="remainingDeepDanbooruSuggestions.length > 1"
                  type="button"
                  class="btn-secondary btn-sm"
                  @click="addAllDeepDanbooruSuggestions"
                >Add All</button>
              </div>
            </div>
            <p v-if="deepdanbooruError" class="text-error">{{ deepdanbooruError }}</p>
            <p v-else-if="!deepdanbooruStatus.loaded" class="text-muted">Checking DeepDanbooru availability…</p>
            <p v-else-if="!deepdanbooruStatus.available" class="text-muted">{{ deepdanbooruStatus.reason }}</p>
            <p v-else-if="isVideo" class="text-muted">AI tagging is available for image uploads. Tag videos after posting once a thumbnail exists.</p>
            <p v-else-if="!file" class="text-muted">Choose an image to generate suggestions.</p>
            <label v-if="deepdanbooruStatus.available && !isVideo && file" class="text-muted deepdanbooru-autoapply">
              <input v-model="deepdanbooruAutoApplyRating" type="checkbox" />
              Auto-apply suggested rating on analyze
            </label>
            <p v-if="deepdanbooruSuggestedRating" class="text-muted">
              Suggested rating: <strong>{{ ratingLabel(deepdanbooruSuggestedRating) }}</strong>
              <span v-if="deepdanbooruSuggestedRatingScore !== null">({{ formatScore(deepdanbooruSuggestedRatingScore) }})</span>
              <button
                type="button"
                class="btn-secondary btn-sm"
                :disabled="rating === normalizedSuggestedRating"
                @click="applySuggestedRating"
              >Use</button>
            </p>
            <div v-if="remainingDeepDanbooruSuggestions.length" class="deepdanbooru-suggestions">
              <button
                v-for="suggestion in remainingDeepDanbooruSuggestions"
                :key="suggestion.tag"
                type="button"
                class="deepdanbooru-chip"
                :class="`tag-${suggestion.type}`"
                @click="addDeepDanbooruSuggestion(suggestion)"
              >
                <span>{{ suggestion.name }}</span>
                <small>{{ formatScore(suggestion.score) }}</small>
              </button>
            </div>
            <p v-else-if="deepdanbooruStatus.available && deepdanbooruSuggestions.length" class="text-muted">All suggested tags are already in this draft.</p>
          </div>

          <div class="field">
            <label>Rating</label>
            <div class="rating-row">
              <button type="button" class="rating-pill" :class="{ active: rating === 's' }" @click="rating = 's'">Safe</button>
              <button type="button" class="rating-pill" :class="{ active: rating === 'q' }" @click="rating = 'q'">Questionable</button>
              <button type="button" class="rating-pill" :class="{ active: rating === 'e' }" @click="rating = 'e'">Explicit</button>
            </div>
          </div>

          <div class="field">
            <label>Source URL</label>
            <input v-model="source" placeholder="https://..." />
            <p v-if="source && !sourceLooksValid" class="text-error">Source must be a valid http/https URL.</p>
          </div>

          <div class="field">
            <label>Description</label>
            <textarea v-model="description" rows="4" maxlength="2000" placeholder="Optional notes or context" />
            <p class="field-hint">{{ description.length }}/2000</p>
          </div>
        </section>

        <div class="action-bar">
          <div class="action-meta">
            <p v-if="error" class="text-error">{{ error }}</p>
            <p v-else-if="uploading" class="text-muted">Uploading media and processing tags...</p>
            <p v-else class="text-muted">Draft saves automatically in this browser.</p>
          </div>
          <div class="action-buttons">
            <button type="button" class="btn-secondary" @click="resetForm" :disabled="uploading">Reset</button>
            <button type="submit" :disabled="uploading">{{ uploading ? 'Uploading...' : 'Upload Post' }}</button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'

const router = useRouter()

const DRAFT_KEY = 'onani-upload-draft-v1'
const NEW_TAG_TYPES = [
  { key: 'GENERAL', label: 'general', prefix: '', className: 'general' },
  { key: 'ARTIST', label: 'artist', prefix: 'artist:', className: 'artist' },
  { key: 'CHARACTER', label: 'character', prefix: 'character:', className: 'character' },
  { key: 'COPYRIGHT', label: 'copyright', prefix: 'copyright:', className: 'copyright' },
  { key: 'META', label: 'meta', prefix: 'meta:', className: 'meta' },
]

const file = ref(null)
const fileInput = ref(null)
const previewUrl = ref('')
const dragActive = ref(false)
const tagInput = ref(null)

const tags = ref([])
const tagDraft = ref('')
const tagSuggestions = ref([])
const tagSuggestionIndex = ref(-1)
let tagSuggestTimer = null

const rating = ref('s')
const source = ref('')
const description = ref('')
const uploading = ref(false)
const error = ref('')
const deepdanbooruStatus = ref({ loaded: false, available: false, reason: '', threshold: 0.5 })
const deepdanbooruLoading = ref(false)
const deepdanbooruSuggestions = ref([])
const deepdanbooruSuggestedRating = ref('')
const deepdanbooruSuggestedRatingScore = ref(null)
const deepdanbooruAutoApplyRating = ref(false)
const deepdanbooruError = ref('')

const isVideo = computed(() => !!file.value?.type?.startsWith('video/'))
const canSuggestWithDeepDanbooru = computed(() => deepdanbooruStatus.value.available && !!file.value && !isVideo.value)
const normalizedTagDraft = computed(() => normalizeTag(tagDraft.value))
const exactSuggestionTypes = computed(() => {
  const draft = normalizedTagDraft.value
  const types = new Set()
  if (!draft) return types
  for (const suggestion of tagSuggestions.value) {
    if (normalizeTag(suggestion.name) === draft) {
      types.add(normalizeSuggestionType(suggestion.type))
    }
  }
  return types
})
const newTagActions = computed(() => {
  const draft = normalizedTagDraft.value
  if (!draft || draft.includes(':')) return []

  return NEW_TAG_TYPES
    .filter(type => !exactSuggestionTypes.value.has(type.key))
    .map(type => ({
      ...type,
      value: `${type.prefix}${draft}`,
    }))
    .filter(action => !tags.value.includes(action.value))
})

const sourceLooksValid = computed(() => {
  if (!source.value) return true
  try {
    const parsed = new URL(source.value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
})
const remainingDeepDanbooruSuggestions = computed(() => {
  return deepdanbooruSuggestions.value.filter(item => !tags.value.includes(item.tag))
})
const normalizedSuggestedRating = computed(() => normalizeSuggestedRating(deepdanbooruSuggestedRating.value))

onMounted(() => {
  loadDraft()
  fetchDeepDanbooruStatus()
})

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  if (tagSuggestTimer) clearTimeout(tagSuggestTimer)
})

watch([tags, rating, source, description], () => {
  persistDraft()
}, { deep: true })

function normalizeTag(raw) {
  return raw.trim().toLowerCase().replace(/\s+/g, '_')
}

function normalizeSuggestionType(type) {
  return String(type || 'GENERAL').toUpperCase()
}

function addTag(raw) {
  const tag = normalizeTag(raw)
  if (!tag || tags.value.includes(tag)) return
  tags.value.push(tag)
}

function commitTagDraft() {
  if (tagSuggestionIndex.value >= 0 && tagSuggestions.value[tagSuggestionIndex.value]) {
    applySuggestion(tagSuggestions.value[tagSuggestionIndex.value].name)
    return
  }
  const parts = tagDraft.value.split(/\s+/).filter(Boolean)
  parts.forEach(addTag)
  tagDraft.value = ''
  tagSuggestions.value = []
  tagSuggestionIndex.value = -1
}

function backspaceTag(event) {
  if (!tagDraft.value && tags.value.length) {
    event.preventDefault()
    tags.value.pop()
  }
}

function removeTag(tag) {
  tags.value = tags.value.filter(t => t !== tag)
}

function focusTagInput() {
  tagInput.value?.focus()
}

function applySuggestion(name) {
  addTag(name)
  tagDraft.value = ''
  tagSuggestions.value = []
  tagSuggestionIndex.value = -1
  focusTagInput()
}

function applyNewTypedTag(action) {
  addTag(action.value)
  tagDraft.value = ''
  tagSuggestions.value = []
  tagSuggestionIndex.value = -1
  focusTagInput()
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

async function suggestTagsWithDeepDanbooru() {
  if (!canSuggestWithDeepDanbooru.value) return
  deepdanbooruLoading.value = true
  deepdanbooruError.value = ''
  try {
    const form = new FormData()
    form.append('file', file.value)
    const { data } = await api.post('/posts/auto-tags', form)
    deepdanbooruSuggestions.value = data.data || []
    deepdanbooruSuggestedRating.value = data.rating || ''
    deepdanbooruSuggestedRatingScore.value = typeof data.rating_score === 'number' ? data.rating_score : null
    if (deepdanbooruAutoApplyRating.value && normalizedSuggestedRating.value) {
      rating.value = normalizedSuggestedRating.value
    }
  } catch (err) {
    deepdanbooruError.value = err.response?.data?.message || 'Could not generate AI tags.'
    deepdanbooruSuggestions.value = []
    deepdanbooruSuggestedRating.value = ''
    deepdanbooruSuggestedRatingScore.value = null
  } finally {
    deepdanbooruLoading.value = false
  }
}

function normalizeSuggestedRating(value) {
  if (value === 'g') return 's'
  if (value === 'q' || value === 's' || value === 'e') return value
  return ''
}

function applySuggestedRating() {
  const nextRating = normalizedSuggestedRating.value
  if (!nextRating) return
  rating.value = nextRating
}

function addDeepDanbooruSuggestion(suggestion) {
  addTag(suggestion.tag)
}

function addAllDeepDanbooruSuggestions() {
  for (const suggestion of remainingDeepDanbooruSuggestions.value) {
    addTag(suggestion.tag)
  }
}

function hideSuggestionsDelayed() {
  window.setTimeout(() => {
    tagSuggestions.value = []
    tagSuggestionIndex.value = -1
  }, 150)
}

function onTagKeydown(event) {
  if (tagSuggestions.value.length) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      tagSuggestionIndex.value = Math.min(tagSuggestionIndex.value + 1, tagSuggestions.value.length - 1)
      return
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault()
      tagSuggestionIndex.value = Math.max(tagSuggestionIndex.value - 1, -1)
      return
    }
    if ((event.key === 'Enter' || event.key === 'Tab') && tagSuggestionIndex.value >= 0) {
      event.preventDefault()
      applySuggestion(tagSuggestions.value[tagSuggestionIndex.value].name)
      return
    }
    if (event.key === 'Escape') {
      tagSuggestions.value = []
      tagSuggestionIndex.value = -1
      return
    }
  }

  if (event.key === 'Enter' || event.key === ' ') {
    const draft = tagDraft.value.trim()
    if (draft) {
      event.preventDefault()
      commitTagDraft()
    }
  }
}

async function onTagInput() {
  if (tagSuggestTimer) clearTimeout(tagSuggestTimer)
  const query = normalizeTag(tagDraft.value)
  tagSuggestionIndex.value = -1
  if (query.length < 1) {
    tagSuggestions.value = []
    return
  }

  tagSuggestTimer = setTimeout(async () => {
    try {
      const { data } = await api.get('/tags/autocomplete', { params: { query } })
      tagSuggestions.value = (data.data || []).filter(t => !tags.value.includes(t.name)).slice(0, 8)
      tagSuggestionIndex.value = tagSuggestions.value.length ? 0 : -1
    } catch {
      tagSuggestions.value = []
      tagSuggestionIndex.value = -1
    }
  }, 180)
}

function openFilePicker() {
  fileInput.value?.click()
}

function setFile(nextFile) {
  if (!nextFile) return
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = nextFile
  previewUrl.value = URL.createObjectURL(nextFile)
  error.value = ''
  deepdanbooruError.value = ''
  deepdanbooruSuggestions.value = []
}

function onNativeFileChange(event) {
  const nextFile = event.target.files?.[0]
  setFile(nextFile)
}

function onDrop(event) {
  dragActive.value = false
  const nextFile = event.dataTransfer?.files?.[0]
  setFile(nextFile)
}

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  file.value = null
  deepdanbooruSuggestions.value = []
  deepdanbooruSuggestedRating.value = ''
  deepdanbooruSuggestedRatingScore.value = null
  deepdanbooruError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let i = 0
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i += 1
  }
  return `${size.toFixed(size >= 100 || i === 0 ? 0 : 1)} ${units[i]}`
}

function formatScore(score) {
  return Number(score).toFixed(2)
}

function ratingLabel(r) {
  return { g: 'General', q: 'Questionable', s: 'Sensitive', e: 'Explicit' }[r] ?? String(r || '').toUpperCase()
}

function persistDraft() {
  const payload = {
    tags: tags.value,
    rating: rating.value,
    source: source.value,
    description: description.value,
  }
  localStorage.setItem(DRAFT_KEY, JSON.stringify(payload))
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const draft = JSON.parse(raw)
    tags.value = Array.isArray(draft.tags) ? draft.tags : []
    rating.value = ['s', 'q', 'e'].includes(draft.rating) ? draft.rating : 's'
    source.value = typeof draft.source === 'string' ? draft.source : ''
    description.value = typeof draft.description === 'string' ? draft.description : ''
  } catch {
    localStorage.removeItem(DRAFT_KEY)
  }
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
}

function resetForm() {
  clearFile()
  tags.value = []
  tagDraft.value = ''
  tagSuggestions.value = []
  rating.value = 's'
  source.value = ''
  description.value = ''
  error.value = ''
  deepdanbooruSuggestions.value = []
  deepdanbooruSuggestedRating.value = ''
  deepdanbooruSuggestedRatingScore.value = null
  deepdanbooruError.value = ''
  clearDraft()
}

async function handleUpload() {
  if (!file.value) {
    error.value = 'Please choose a file first.'
    return
  }
  if (!tags.value.length) {
    error.value = 'Add at least one tag.'
    return
  }
  if (!sourceLooksValid.value) {
    error.value = 'Source URL must be valid.'
    return
  }

  uploading.value = true
  error.value = ''

  const form = new FormData()
  form.append('file', file.value)
  form.append('tags', tags.value.join(' '))
  form.append('rating', rating.value)
  form.append('source', source.value.trim())
  form.append('description', description.value.trim())

  try {
    const { data } = await api.post('/posts/upload', form)
    clearDraft()
    router.push(`/posts/${data.id}`)
  } catch (err) {
    error.value = err.response?.data?.message || 'Upload failed.'
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-page {
  width: min(72rem, 100%);
  margin: 0 auto;
}

.upload-layout {
  display: grid;
  grid-template-columns: 16rem minmax(0, 1fr);
  gap: 1rem;
}

.upload-sidebar {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem;
  align-self: start;
  position: sticky;
  top: 1rem;
}

.tips-card {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
  border-radius: 0;
}

.tips-card h3 {
  font-size: 0.92rem;
  margin-bottom: 0.45rem;
}

.tips-card ul {
  display: grid;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.upload-content {
  display: grid;
  gap: 1rem;
}

.section-card {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.native-file-input {
  display: none;
}

.drop-zone {
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  background: color-mix(in srgb, var(--bg-overlay) 85%, transparent);
  min-height: 13rem;
  display: grid;
  place-items: center;
  padding: 0.8rem;
  cursor: pointer;
}

.drop-zone.active {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, var(--bg-overlay));
}

.drop-placeholder {
  text-align: center;
  display: grid;
  gap: 0.25rem;
}

.media-preview {
  width: 100%;
  max-height: 24rem;
  object-fit: contain;
  background: var(--bg-overlay);
  border-radius: var(--radius-xs);
}

.file-meta-row {
  margin-top: 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}

.status-badge {
  padding: 0.15em 0.5em;
  border-radius: var(--radius-xs);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-pending {
  background: #5a4d2d;
  color: #dfcf8f;
}

.field {
  display: grid;
  gap: 0.35rem;
  margin-bottom: 0.9rem;
}

.field:last-child {
  margin-bottom: 0;
}

.field label {
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  font-weight: 600;
}

.field-hint {
  font-size: 0.78rem;
  color: var(--text-dim);
}

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.deepdanbooru-actions {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.deepdanbooru-field {
  padding-top: 0.2rem;
}

.deepdanbooru-autoapply {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.4rem;
}

.tag-input-wrap {
  position: relative;
}

.tag-editor {
  min-height: 2.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-overlay);
  padding: 0.35rem;
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
  align-items: center;
}

.tag-editor input {
  border: none;
  padding: 0.35rem 0.2rem;
  min-width: 10rem;
  flex: 1;
  background: transparent;
}

.tag-editor input:focus {
  background: transparent;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--item-hover);
  color: var(--text);
  padding: 0.2rem 0.45rem;
  font-size: 0.8rem;
  border-radius: var(--radius-xs);
}

.tag-remove {
  border: none;
  background: none;
  color: var(--text-muted);
  padding: 0;
  width: 1rem;
  height: 1rem;
  line-height: 1;
}

.tag-remove:hover {
  color: var(--error);
  background: none;
}

.autocomplete-list {
  position: absolute;
  top: calc(100% + 0.25rem);
  left: 0;
  right: 0;
  z-index: 20;
  margin: 0;
  padding: 0.25rem 0;
  list-style: none;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  max-height: 14rem;
  overflow-y: auto;
}

.new-tag-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.5rem;
}

.new-tag-btn {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  padding: 0.28rem 0.55rem;
  font-size: 0.78rem;
  line-height: 1.2;
}

.new-tag-btn:hover {
  background: var(--item-hover);
}

.autocomplete-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.65rem;
  cursor: pointer;
  border-left: 3px solid transparent;
}

.autocomplete-item:hover,
.autocomplete-item.active {
  background: var(--item-hover);
}

.ac-name {
  font-weight: 600;
}

.ac-count {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.rating-row {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.deepdanbooru-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.deepdanbooru-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  font-size: 0.82rem;
  padding: 0.35rem 0.6rem;
}

.deepdanbooru-chip small {
  color: var(--text-muted);
}

.rating-pill {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.rating-pill.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-meta p {
  margin: 0;
}

@media (max-width: 900px) {
  .upload-layout {
    grid-template-columns: 1fr;
  }

  .upload-sidebar {
    position: static;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .action-buttons {
    justify-content: flex-end;
  }

  .field-label-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
