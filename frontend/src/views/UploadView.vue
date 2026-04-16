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
import { ref } from 'vue'
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

function onFileChange(e) {
  file.value = e.target.files[0]
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
</style>
