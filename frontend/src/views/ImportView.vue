<template>
  <div class="page-container import-page">
    <h1>Import</h1>
    <p class="text-muted">Paste a URL from any supported site (Danbooru, Gelbooru, Rule34, Pixiv, DeviantArt, and <a href="https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md" target="_blank" rel="noopener">900+ more</a>).</p>

    <form class="import-form" @submit.prevent="startImport">
      <input v-model="url" placeholder="https://danbooru.donmai.us/posts/12345" required />
      <button type="submit" :disabled="importing">{{ importing ? 'Importing...' : 'Import' }}</button>
    </form>

    <p v-if="error" class="text-error">{{ error }}</p>

    <fieldset class="cookies-section">
      <legend>Import Cookies</legend>
      <p class="text-muted">Upload a Netscape-format cookies.txt file for gallery-dl. It will be stored encrypted with your password.</p>
      <p v-if="hasCookies" class="cookies-status">Cookies file stored.</p>
      <div class="field">
        <label>Password (required)</label>
        <input v-model="cookiePassword" type="password" autocomplete="current-password" />
      </div>
      <div class="field">
        <input type="file" ref="cookieFileInput" accept=".txt,.cookies" />
      </div>
      <div class="cookies-actions">
        <button @click="uploadCookies" :disabled="cookieUploading">{{ cookieUploading ? 'Uploading...' : 'Upload Cookies' }}</button>
        <button v-if="hasCookies" @click="deleteCookies" class="btn-danger">Remove Cookies</button>
      </div>
      <p v-if="cookieError" class="text-error">{{ cookieError }}</p>
      <p v-if="cookieSuccess" class="text-success">{{ cookieSuccess }}</p>
    </fieldset>

    <div v-for="job in jobs" :key="job.id" class="import-job" :class="{ expanded: job.expanded }">
      <div class="job-header" @click="job.expanded = !job.expanded">
        <span class="status-dot" :class="dotClass(job)"></span>
        <span class="job-url">{{ job.url }}</span>
        <span class="job-elapsed text-muted">{{ elapsed(job) }}</span>
        <span class="status-badge" :class="badgeClass(job)">{{ displayStatus(job) }}</span>
        <button class="btn-dismiss" @click.stop="dismissJob(job.id)" title="Dismiss">✕</button>
      </div>

      <div v-if="job.expanded" class="job-body">
        <!-- Progress bar -->
        <div v-if="job.meta && job.meta.total" class="progress-bar">
          <div class="progress-fill" :style="{ width: (job.meta.current / job.meta.total * 100) + '%' }"></div>
          <span class="progress-label">{{ job.meta.current }} / {{ job.meta.total }}</span>
        </div>

        <!-- Logs -->
        <div v-if="job.logs.length" class="import-logs">
          <pre class="log-output" ref="logRefs">{{ job.logs.join('\n') }}</pre>
        </div>
        <p v-else class="text-muted" style="font-size:0.85rem">Waiting for logs...</p>

        <!-- Results -->
        <template v-if="job.status === 'SUCCESS' && job.result && !job.result.error">
          <p class="import-count">Imported {{ job.result.count }} post{{ job.result.count !== 1 ? 's' : '' }}</p>
          <div class="import-posts-grid">
            <router-link
              v-for="post in job.result.posts.filter(p => p.post_id)"
              :key="post.post_id"
              :to="`/posts/${post.post_id}`"
              class="post-thumb"
            >
              <img :src="post.thumbnail_url" :alt="`Post #${post.post_id}`" loading="lazy" :class="{ 'sfw-blurred': shouldBlur(post, post.post_id) }" />
              <div v-if="shouldBlur(post, post.post_id)" class="sfw-overlay" @click.stop="reveal(post.post_id)">Show</div>
            </router-link>
          </div>
          <ul v-if="job.result.posts.some(p => p.error)" class="error-list">
            <li v-for="(post, i) in job.result.posts.filter(p => p.error)" :key="i" class="text-error">
              {{ post.file_url }}: {{ post.error }}
            </li>
          </ul>
        </template>

        <p v-else-if="job.status === 'SUCCESS' && job.result && job.result.error" class="text-error">{{ job.result.error }}</p>
        <p v-else-if="job.status === 'FAILURE'" class="text-error">{{ job.result }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useSfwMode } from '@/composables/useSfwMode'

const auth = useAuthStore()
const { shouldBlur, reveal } = useSfwMode()

const url = ref('')
const importing = ref(false)
const error = ref('')

const hasCookies = ref(false)
const cookiePassword = ref('')
const cookieUploading = ref(false)
const cookieError = ref('')
const cookieSuccess = ref('')
const cookieFileInput = ref(null)
const jobs = reactive([])
const timers = {}
let elapsedInterval = null

const STORAGE_KEY = 'importJobs'
const MAX_HISTORY = 50
const now = ref(Date.now())

function jobFailed(job) {
  return job.status === 'FAILURE' || job.status === 'ERROR' || (job.status === 'SUCCESS' && !!job.result?.error)
}
function jobSucceeded(job) {
  return job.status === 'SUCCESS' && !job.result?.error
}

function saveJobs() {
  const toSave = jobs.slice(0, MAX_HISTORY).map(j => ({
    id: j.id, url: j.url, status: j.status, result: j.result,
    meta: j.meta, logs: j.logs, startedAt: j.startedAt, finishedAt: j.finishedAt,
  }))
  localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
}

function dotClass(job) {
  if (jobSucceeded(job)) return 'dot-success'
  if (jobFailed(job)) return 'dot-failure'
  return 'dot-pending'
}

function badgeClass(job) {
  return {
    'status-success': jobSucceeded(job),
    'status-failure': jobFailed(job),
    'status-pending': !jobSucceeded(job) && !jobFailed(job),
  }
}

function displayStatus(job) {
  if (jobFailed(job)) return 'FAILED'
  if (job.status === 'PROGRESS' && job.meta) return `${job.meta.current}/${job.meta.total}`
  return job.status
}

function elapsed(job) {
  const ms = (job.finishedAt || now.value) - job.startedAt
  const secs = Math.floor(ms / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  const rem = secs % 60
  return `${mins}m ${rem}s`
}

onMounted(() => {
  elapsedInterval = setInterval(() => { now.value = Date.now() }, 1000)
  if (auth.user) loadCookieStatus()
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    for (const s of saved) {
      const finished = ['SUCCESS', 'FAILURE', 'ERROR'].includes(s.status)
      const job = {
        id: s.id, url: s.url,
        status: s.status || 'PENDING',
        result: s.result || null,
        meta: s.meta || null,
        logs: s.logs || [],
        expanded: !finished,
        startedAt: s.startedAt || Date.now(),
        finishedAt: s.finishedAt || null,
      }
      jobs.push(job)
      if (!finished) pollJob(job)
    }
  } catch { /* ignore corrupt data */ }
})

onUnmounted(() => {
  Object.values(timers).forEach(clearTimeout)
  if (elapsedInterval) clearInterval(elapsedInterval)
})

async function startImport() {
  importing.value = true
  error.value = ''
  try {
    const { data } = await api.post('/import', { url: url.value })
    const job = { id: data.id, url: url.value, status: 'PENDING', result: null, meta: null, logs: [], expanded: true, startedAt: Date.now(), finishedAt: null }
    jobs.unshift(job)
    saveJobs()
    pollJob(job)
    url.value = ''
  } catch (err) {
    error.value = err.response?.data?.message || 'Import failed.'
  } finally {
    importing.value = false
  }
}

async function pollJob(job) {
  if (timers[job.id]) clearTimeout(timers[job.id])
  try {
    const { data } = await api.get('/import', { params: { id: job.id } })
    job.status = data.status

    if (data.meta) {
      job.meta = data.meta
      if (data.meta.logs) job.logs = data.meta.logs
    }

    if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
      job.result = data.result
      job.finishedAt = Date.now()
      if (data.result?.logs) job.logs = data.result.logs
      delete timers[job.id]
      saveJobs()
    } else {
      timers[job.id] = setTimeout(() => pollJob(job), 2000)
    }
  } catch {
    job.status = 'ERROR'
    job.finishedAt = Date.now()
    saveJobs()
    delete timers[job.id]
  }
}

function dismissJob(id) {
  if (timers[id]) { clearTimeout(timers[id]); delete timers[id] }
  const idx = jobs.findIndex(j => j.id === id)
  if (idx !== -1) jobs.splice(idx, 1)
  saveJobs()
}

async function loadCookieStatus() {
  try {
    const { data } = await api.get('/profile/cookies')
    hasCookies.value = data.has_cookies
  } catch { /* ignore */ }
}

async function uploadCookies() {
  cookieError.value = ''
  cookieSuccess.value = ''
  if (!cookiePassword.value) { cookieError.value = 'Password is required.'; return }
  const file = cookieFileInput.value?.files?.[0]
  if (!file) { cookieError.value = 'Select a cookies file.'; return }
  cookieUploading.value = true
  try {
    const form = new FormData()
    form.append('password', cookiePassword.value)
    form.append('cookies', file)
    const { data } = await api.post('/profile/cookies', form)
    cookieSuccess.value = data.message
    hasCookies.value = true
    cookiePassword.value = ''
  } catch (err) {
    cookieError.value = err.response?.data?.message || 'Upload failed.'
  } finally {
    cookieUploading.value = false
  }
}

async function deleteCookies() {
  cookieError.value = ''
  cookieSuccess.value = ''
  try {
    const { data } = await api.delete('/profile/cookies')
    cookieSuccess.value = data.message
    hasCookies.value = false
  } catch (err) {
    cookieError.value = err.response?.data?.message || 'Remove failed.'
  }
}
</script>

<style scoped>
.import-page { max-width: 700px; margin-left: auto; margin-right: auto; }
.import-form { display: flex; gap: 0.5rem; }
.import-form input { flex: 1; }

.import-job {
  margin-top: 0.75rem;
  background: var(--bg-overlay);
  border-radius: 6px;
  overflow: hidden;
}

.job-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  cursor: pointer;
  user-select: none;
}
.job-header:hover { background: var(--item-hover); }

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-success { background: #8fdf8f; }
.dot-failure { background: #df8f8f; }
.dot-pending { background: #dfcf8f; animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.job-url {
  flex: 1;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.job-elapsed {
  font-size: 0.75rem;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.btn-dismiss {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0 0.25em;
  line-height: 1;
  flex-shrink: 0;
}
.btn-dismiss:hover { color: #df8f8f; }

.job-body {
  padding: 0 0.75rem 0.75rem;
}

.progress-bar {
  position: relative;
  height: 1.4rem;
  background: var(--bg-raised, #1a1a1a);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}
.progress-fill {
  height: 100%;
  background: var(--accent, #5a8a5a);
  transition: width 0.3s ease;
}
.progress-label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.import-logs { margin-bottom: 0.75rem; }
.log-output {
  background: var(--bg-raised, #1a1a1a);
  padding: 0.5rem;
  font-size: 0.8rem;
  max-height: 14rem;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  border-radius: 4px;
}

.import-count {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.import-posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(9em, 1fr));
  gap: 0.5em;
}
.import-posts-grid .post-thumb {
  display: block;
  height: 9em;
  overflow: hidden;
}
.import-posts-grid .post-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.error-list {
  list-style: none;
  padding: 0;
  margin-top: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.status-badge {
  padding: 0.15em 0.5em;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  flex-shrink: 0;
}
.status-success { background: #2d5a2d; color: #8fdf8f; }
.status-failure { background: #5a2d2d; color: #df8f8f; }
.status-pending { background: #5a4d2d; color: #dfcf8f; }

.cookies-section { border: 1px solid #444; padding: 0.75rem; border-radius: 6px; margin-top: 1em; }
.cookies-status { color: #8fdf8f; font-size: 0.9rem; margin: 0 0 0.5em; }
.cookies-actions { display: flex; gap: 0.5em; margin-top: 0.5em; }
.field { display: flex; flex-direction: column; gap: 0.25rem; }
.field label { font-weight: 600; }
.btn-danger { background: #5a2d2d; color: #df8f8f; border: none; cursor: pointer; padding: 6px 12px; border-radius: 4px; }
.btn-danger:hover { background: #7a3d3d; }
.text-success { color: #6f6; }
</style>
