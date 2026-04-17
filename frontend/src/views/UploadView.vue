<template>
  <div class="page-container upload-page">
    <h1>Upload</h1>
    <form @submit.prevent="handleUpload" class="upload-form">
      <div class="field">
        <label>File</label>
        <input type="file" @change="onFileChange" accept="image/*,video/*" required />
      </div>
      <div class="field">
        <label>Tags (space-separated)</label>
        <input v-model="tags" placeholder="tag1 tag2 tag3" required />
      </div>
      <div class="field">
        <label>Rating</label>
        <select v-model="rating" required>
          <option value="s">Safe</option>
          <option value="q">Questionable</option>
          <option value="e">Explicit</option>
        </select>
        <div v-if="ratingAnalyzing" class="suggestion suggestion--loading">
          Analyzing image…
        </div>
        <div v-else-if="ratingSuggestion" class="suggestion">
          Suggested rating: <strong>{{ ratingSuggestionLabel }}</strong>
          <button type="button" class="suggestion-apply" @click="applyRatingSuggestion">Apply</button>
        </div>
      </div>
      <div class="field">
        <label>Source URL</label>
        <input v-model="source" placeholder="https://..." />
      </div>
      <div class="field">
        <label>Description</label>
        <textarea v-model="description" rows="3"></textarea>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="uploading">{{ uploading ? 'Uploading...' : 'Upload' }}</button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'

const router = useRouter()

const file = ref(null)
const tags = ref('')
const rating = ref('s')
const source = ref('')
const description = ref('')
const uploading = ref(false)
const error = ref('')

const ratingAnalyzing = ref(false)
const ratingSuggestion = ref(null)

const RATING_LABELS = { s: 'Safe', q: 'Questionable', e: 'Explicit' }

const ratingSuggestionLabel = computed(() =>
  ratingSuggestion.value ? RATING_LABELS[ratingSuggestion.value] : ''
)

function applyRatingSuggestion() {
  if (ratingSuggestion.value) rating.value = ratingSuggestion.value
}

function classifyToRating(predictions) {
  const best = predictions.reduce((a, b) => (a.probability > b.probability ? a : b))
  if (best.className === 'Porn' || best.className === 'Hentai') return 'e'
  if (best.className === 'Sexy') return 'q'
  return 's'
}

async function analyzeImage(imgFile) {
  ratingAnalyzing.value = true
  ratingSuggestion.value = null
  let objectUrl = null
  try {
    const { load } = await import('nsfwjs')
    objectUrl = URL.createObjectURL(imgFile)
    const img = new Image()
    await new Promise((resolve, reject) => {
      img.onload = resolve
      img.onerror = reject
      img.src = objectUrl
    })
    const model = await load()
    const predictions = await model.classify(img)
    ratingSuggestion.value = classifyToRating(predictions)
  } catch {
    // Silent failure — user can still pick rating manually
  } finally {
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    ratingAnalyzing.value = false
  }
}

function onFileChange(e) {
  const selected = e.target.files[0]
  file.value = selected
  ratingSuggestion.value = null

  if (selected && selected.type.startsWith('image/')) {
    analyzeImage(selected)
  }
}

async function handleUpload() {
  if (!file.value) return
  uploading.value = true
  error.value = ''

  const form = new FormData()
  form.append('file', file.value)
  form.append('tags', tags.value)
  form.append('rating', rating.value)
  form.append('source', source.value)
  form.append('description', description.value)

  try {
    const { data } = await api.post('/posts/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    router.push(`/posts/${data.id}`)
  } catch (err) {
    error.value = err.response?.data?.message || 'Upload failed.'
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-page { max-width: 600px; margin-left: auto; margin-right: auto; }
.upload-form { display: flex; flex-direction: column; gap: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.25rem; }
.field label { font-weight: 600; }
.error { color: #f66; }
.suggestion {
  font-size: 0.85rem;
  color: #aaa;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.suggestion strong { color: #ddd; }
.suggestion--loading { font-style: italic; }
.suggestion-apply {
  background: none;
  border: 1px solid #888;
  border-radius: 4px;
  color: #ccc;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 1px 6px;
}
.suggestion-apply:hover { border-color: #ccc; color: #fff; }
</style>
