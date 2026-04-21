<template>
  <div class="import-page page-container">
    <div class="import-layout">
      <aside class="import-sidebar">
        <h1 class="sidebar-title">Import</h1>
        <p class="text-muted sidebar-intro">
          Paste links from supported sites and monitor imports live.
          <a href="https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md" target="_blank" rel="noopener">See supported sites</a>.
        </p>

        <div class="stats-card">
          <h3>Queue Summary</h3>
          <div class="stats-grid">
            <span class="status-badge status-pending">Active: {{ stats.active }}</span>
            <span class="status-badge status-success">Success: {{ stats.success }}</span>
            <span class="status-badge status-failure">Failed: {{ stats.failed }}</span>
            <span class="status-badge">Total: {{ jobs.length }}</span>
          </div>
        </div>

        <div class="cookies-card">
          <h3>Import Cookies</h3>
          <p class="text-muted">Stored encrypted with your password.</p>
          <p v-if="hasCookies" class="text-success">Cookies file stored.</p>

          <div class="field">
            <label>Password</label>
            <input v-model="cookiePassword" type="password" autocomplete="current-password" />
          </div>
          <input type="file" ref="cookieFileInput" accept=".txt,.cookies" class="cookie-file-input" />

          <div class="cookies-actions">
            <button type="button" class="btn-secondary btn-sm" @click="uploadCookies" :disabled="cookieUploading">
              {{ cookieUploading ? 'Uploading...' : 'Upload Cookies' }}
            </button>
            <button type="button" class="btn-danger btn-sm" v-if="hasCookies" @click="deleteCookies">Remove</button>
          </div>

          <p v-if="cookieError" class="text-error">{{ cookieError }}</p>
          <p v-if="cookieSuccess" class="text-success">{{ cookieSuccess }}</p>
        </div>
      </aside>

      <div class="import-content">
        <div class="view-tabs">
          <button
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'imports' }"
            @click="activeTab = 'imports'"
          >
            Imports
          </button>
          <button
            v-if="isAdmin"
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'scheduler' }"
            @click="activeTab = 'scheduler'"
          >
            Scheduler
          </button>
        </div>

        <section v-show="activeTab === 'imports'" class="section-card">
          <h2>Start Import</h2>
          <div class="single-import-row">
            <input v-model="singleUrl" placeholder="https://example.com/post/123" @keyup.enter="startSingleImport" />
            <button @click="startSingleImport" :disabled="importingSingle">{{ importingSingle ? 'Starting...' : 'Import' }}</button>
          </div>

          <div class="batch-area">
            <label>Batch URLs (one per line)</label>
            <textarea v-model="batchInput" rows="3" class="compact-textarea" placeholder="https://site/post/1&#10;https://site/post/2" />
            <div class="batch-actions">
              <span class="text-muted">{{ parsedBatchUrls.length }} valid URL{{ parsedBatchUrls.length !== 1 ? 's' : '' }}</span>
              <button class="btn-secondary" @click="startBatchImport" :disabled="importingBatch || !parsedBatchUrls.length">
                {{ importingBatch ? 'Queueing...' : 'Queue Batch' }}
              </button>
              <button class="btn-secondary" @click="batchInput = ''" :disabled="importingBatch || !batchInput">Clear</button>
            </div>
          </div>

          <p v-if="error" class="text-error">{{ error }}</p>
        </section>

        <section v-if="isAdmin" v-show="activeTab === 'scheduler'" class="section-card">
          <div class="section-head">
            <h2>Scheduler</h2>
            <div class="job-tools">
              <input v-model="scheduledSearch" class="admin-inline-input" placeholder="Search label or URL" />
              <button class="btn-secondary btn-sm" @click="fetchScheduledTasks">Refresh</button>
              <button class="btn-secondary btn-sm" @click="openNewScheduledForm">New</button>
            </div>
          </div>

          <div v-if="scheduledFormVisible" class="scheduled-form">
            <h3>{{ scheduledEditId !== null ? 'Edit Scheduled Import' : 'New Scheduled Import' }}</h3>
            <div class="form-row">
              <label>URL</label>
              <input v-model="scheduledForm.url" type="url" placeholder="https://example.com/gallery" class="full-width" />
            </div>
            <div class="form-row">
              <label>Label</label>
              <input v-model="scheduledForm.label" type="text" placeholder="Optional label" class="full-width" />
            </div>
            <div class="form-row">
              <label>Interval</label>
              <select v-model="scheduledForm.interval_minutes" class="full-width">
                <option v-for="opt in INTERVAL_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div class="form-row form-row-inline">
              <label>Enabled</label>
              <input v-model="scheduledForm.enabled" type="checkbox" />
            </div>
            <div class="form-row">
              <label>Cookies (optional)</label>
              <textarea v-model="scheduledForm.cookies" rows="2" class="full-width compact-textarea" placeholder="# Netscape/header format"></textarea>
            </div>
            <div class="form-actions">
              <button type="button" @click="saveScheduledTask">{{ scheduledEditId !== null ? 'Save' : 'Create' }}</button>
              <button type="button" class="btn-secondary" @click="cancelScheduledForm">Cancel</button>
            </div>
          </div>

          <p class="text-muted" v-if="scheduledLoading">Loading scheduler tasks...</p>
          <p class="text-muted" v-else-if="!filteredScheduledTasks.length">No scheduled imports yet.</p>

          <div v-else class="table-wrap">
            <table class="scheduled-table">
              <thead>
                <tr>
                  <th>Label / URL</th>
                  <th>Interval</th>
                  <th>Last Run</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in filteredScheduledTasks" :key="task.id" :class="{ 'task-disabled': !task.enabled }">
                  <td>
                    <div class="task-primary">
                      <span class="task-status-dot" :class="scheduledDotClass(task)"></span>
                      <div>
                        <strong v-if="task.label">{{ task.label }}</strong>
                        <div class="text-muted task-url-text">{{ task.url }}</div>
                      </div>
                    </div>
                  </td>
                  <td>{{ intervalLabel(task.interval_minutes) }}</td>
                  <td>{{ task.last_run_at ? formatDate(task.last_run_at) : 'Never' }}</td>
                  <td class="task-actions">
                    <button type="button" class="btn-secondary btn-sm btn-icon" :title="task.enabled ? 'Disable task' : 'Enable task'" @click="toggleScheduledEnabled(task)">{{ task.enabled ? '◼' : '◻' }}</button>
                    <button type="button" class="btn-secondary btn-sm btn-icon" title="Edit task" @click="openEditScheduledForm(task)">✎</button>
                    <button type="button" class="btn-secondary btn-sm btn-icon" title="Run now" @click="runScheduledTaskNow(task)">▶</button>
                    <button type="button" class="btn-danger btn-sm btn-icon" title="Delete task" @click="deleteScheduledTask(task)">✕</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section v-show="activeTab === 'imports'" class="section-card">
          <div class="section-head">
            <h2>Import Jobs</h2>
            <div class="job-tools">
              <input v-model="search" class="admin-inline-input" placeholder="Filter by URL or status" />
              <select v-model="statusFilter" class="admin-inline-select">
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="SUCCESS">Success</option>
                <option value="FAILURE">Failed</option>
                <option value="REVOKED">Stopped</option>
              </select>
              <button class="btn-secondary btn-sm" @click="refreshHistory">Refresh</button>
              <button class="btn-secondary btn-sm" @click="clearFinished">Clear Finished</button>
            </div>
          </div>

          <p class="text-muted" v-if="filteredJobs.length !== jobs.length">
            Showing {{ filteredJobs.length }} of {{ jobs.length }} jobs.
          </p>

          <div v-if="filteredJobs.length" class="job-list">
            <article v-for="job in filteredJobs" :key="job.id" class="import-job" :class="{ expanded: job.expanded }">
              <header class="job-header" @click="job.expanded = !job.expanded">
                <span class="status-dot" :class="dotClass(job)"></span>
                <div class="job-meta">
                  <span class="job-elapsed text-muted">{{ elapsed(job) }}</span>
                  <span class="status-badge" :class="badgeClass(job)">{{ displayStatus(job) }}</span>
                </div>

                <div class="job-main">
                  <span class="job-url">{{ job.url }}</span>
                  <span class="job-subtitle text-muted">{{ jobSecondaryText(job) }}</span>
                </div>

                <div class="job-actions" @click.stop>
                  <button
                    v-if="isJobActive(job)"
                    type="button"
                    class="btn-danger btn-sm"
                    @click="stopJob(job)"
                  >Stop</button>
                  <button
                    v-else-if="isJobRetryable(job)"
                    type="button"
                    class="btn-secondary btn-sm"
                    @click="retryJob(job)"
                  >Retry</button>
                  <button v-if="!isJobActive(job)" type="button" class="btn-secondary btn-sm" @click="dismissJob(job.id)">Dismiss</button>
                </div>
              </header>

              <div v-if="job.expanded" class="job-body">
                <div v-if="job.meta && job.meta.total" class="progress-bar">
                  <div class="progress-fill" :style="{ width: progressPercent(job) + '%' }"></div>
                  <span class="progress-label">{{ job.meta.current }} / {{ job.meta.total }}</span>
                </div>

                <div v-if="job.logs.length" class="import-logs">
                  <pre class="log-output">{{ joinLines(job.logs) }}</pre>
                </div>
                <p v-else class="text-muted">Waiting for logs...</p>

                <template v-if="job.status === 'SUCCESS' && job.result && !job.result.error">
                  <p class="import-count">
                    Imported {{ job.result.count }} post{{ job.result.count !== 1 ? 's' : '' }}
                    <span v-if="job.result.collection" class="collection-badge">
                      into
                      <router-link :to="`/collections/${job.result.collection.id}`">{{ job.result.collection.title }}</router-link>
                    </span>
                  </p>

                  <div class="import-posts-grid">
                    <PostThumb
                      v-for="post in visiblePosts(job)"
                      :key="post.post_id"
                      :post="post"
                      :post-id="post.post_id"
                    />
                  </div>

                  <button
                    v-if="successfulPosts(job).length > 6"
                    class="show-more-btn"
                    @click.stop="job.showAllPosts = !job.showAllPosts"
                  >
                    {{ job.showAllPosts ? 'Show fewer posts' : `Show all ${successfulPosts(job).length}` }}
                  </button>

                  <ul v-if="failedPostRows(job).length" class="error-list">
                    <li v-for="(post, idx) in failedPostRows(job)" :key="idx" class="text-error">
                      {{ post.file_url }}: {{ post.error }}
                    </li>
                  </ul>
                </template>

                <p v-else-if="job.status === 'SUCCESS' && job.result?.error" class="text-error">{{ job.result.error }}</p>
                <p v-else-if="job.status === 'FAILURE'" class="text-error">{{ formatFailure(job.result) }}</p>
              </div>
            </article>
          </div>
          <p v-else class="text-muted">No jobs match your filter.</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import PostThumb from '@/components/PostThumb.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const singleUrl = ref('')
const batchInput = ref('')
const importingSingle = ref(false)
const importingBatch = ref(false)
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
const now = ref(Date.now())

const search = ref('')
const statusFilter = ref('')
const activeTab = ref('imports')

const isAdmin = computed(() => Number(auth.user?.role || 0) >= 300)

function normalizeTab(tab) {
  if (tab === 'scheduler' && isAdmin.value) return 'scheduler'
  return 'imports'
}

const INTERVAL_OPTIONS = [
  { value: 30, label: 'Every 30 minutes' },
  { value: 60, label: 'Hourly' },
  { value: 120, label: 'Every 2 hours' },
  { value: 360, label: 'Every 6 hours' },
  { value: 720, label: 'Every 12 hours' },
  { value: 1440, label: 'Daily' },
  { value: 2880, label: 'Every 2 days' },
  { value: 10080, label: 'Weekly' },
]

const scheduledTasks = ref([])
const scheduledLoading = ref(false)
const scheduledSearch = ref('')
const scheduledFormVisible = ref(false)
const scheduledEditId = ref(null)
const scheduledForm = reactive({
  url: '',
  label: '',
  interval_minutes: 1440,
  enabled: true,
  cookies: '',
})

const filteredScheduledTasks = computed(() => {
  const q = scheduledSearch.value.trim().toLowerCase()
  if (!q) return scheduledTasks.value
  return scheduledTasks.value.filter(t => `${t.label || ''} ${t.url || ''}`.toLowerCase().includes(q))
})

const parsedBatchUrls = computed(() => {
  const lines = batchInput.value.split(/[\n\r]+/).map(v => v.trim()).filter(Boolean)
  const deduped = [...new Set(lines)]
  return deduped.filter(isLikelyHttpUrl)
})

const filteredJobs = computed(() => {
  const q = search.value.trim().toLowerCase()
  return jobs.filter(job => {
    const status = displayStatus(job).toLowerCase()
    const url = (job.url || '').toLowerCase()
    const matchesText = !q || status.includes(q) || url.includes(q)
    const matchesStatus = !statusFilter.value
      || (statusFilter.value === 'active' && isJobActive(job))
      || job.status === statusFilter.value
    return matchesText && matchesStatus
  })
})

const stats = computed(() => {
  let active = 0
  let success = 0
  let failed = 0
  for (const job of jobs) {
    if (isJobActive(job)) active += 1
    else if (jobSucceeded(job)) success += 1
    else if (jobFailed(job)) failed += 1
  }
  return { active, success, failed }
})

function isLikelyHttpUrl(value) {
  try {
    const parsed = new URL(value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

function jobFailed(job) {
  return job.status === 'FAILURE' || job.status === 'ERROR' || job.status === 'REVOKED' || (job.status === 'SUCCESS' && !!job.result?.error)
}

function jobSucceeded(job) {
  return job.status === 'SUCCESS' && !job.result?.error
}

function isJobActive(job) {
  return job.status === 'PENDING' || job.status === 'PROGRESS' || job.status === 'QUEUED'
}

function isJobRetryable(job) {
  return !isJobActive(job) && !!job.url && (jobFailed(job) || job.status === 'REVOKED')
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
  if (job.status === 'REVOKED') return 'STOPPED'
  if (job.status === 'QUEUED') return 'QUEUED'
  if (job.status === 'PROGRESS' && job.meta?.total) return `${job.meta.current}/${job.meta.total}`
  if (jobFailed(job)) return 'FAILED'
  return job.status
}

function elapsed(job) {
  const ms = (job.finishedAt || now.value) - job.startedAt
  const totalSecs = Math.floor(ms / 1000)
  if (totalSecs < 60) return `${totalSecs}s`
  const totalMins = Math.floor(totalSecs / 60)
  if (totalMins < 60) return `${totalMins}m ${totalSecs % 60}s`
  const hours = Math.floor(totalMins / 60)
  if (hours < 24) return `${hours}h ${totalMins % 60}m`
  const days = Math.floor(hours / 24)
  return `${days}d ${hours % 24}h`
}

function progressPercent(job) {
  if (!job.meta?.total) return 0
  return Math.max(0, Math.min(100, (job.meta.current / job.meta.total) * 100))
}

function joinLines(lines) {
  return (lines || []).join('\n')
}

function successfulPosts(job) {
  return (job.result?.posts || []).filter(p => p.post_id)
}

function visiblePosts(job) {
  const posts = successfulPosts(job)
  return posts.slice(0, job.showAllPosts ? posts.length : 6)
}

function failedPostRows(job) {
  return (job.result?.posts || []).filter(p => p.error)
}

function formatFailure(result) {
  if (!result) return 'Import failed.'
  if (typeof result === 'string') return result
  if (result.error) return result.error
  return 'Import failed.'
}

function jobSecondaryText(job) {
  if (job.status === 'QUEUED') return 'Waiting for an available worker slot.'
  if (job.status === 'PENDING') return 'Preparing importer task.'
  if (job.status === 'PROGRESS') return 'Import in progress. Click to view logs.'
  if (jobSucceeded(job)) return 'Import completed successfully. Click to inspect results.'
  if (job.status === 'REVOKED') return 'Import was stopped before completion.'
  return 'Import finished with issues. Click to inspect logs.'
}

function mergeServerJob(serverJob) {
  const existing = jobs.find(j => j.id === serverJob.id)
  const finished = ['SUCCESS', 'FAILURE', 'REVOKED', 'ERROR'].includes(serverJob.status)
  const startedAt = serverJob.created_at ? new Date(serverJob.created_at).getTime() : Date.now()
  const finishedAt = serverJob.finished_at ? new Date(serverJob.finished_at).getTime() : null

  if (existing) {
    existing.url = serverJob.url || existing.url
    existing.status = serverJob.status || existing.status
    if (serverJob.result) existing.result = serverJob.result
    if (finished && !existing.finishedAt) existing.finishedAt = finishedAt || Date.now()
    if (serverJob.result?.logs) existing.logs = serverJob.result.logs
    if (!finished && !timers[existing.id]) pollJob(existing)
    return
  }

  const job = {
    id: serverJob.id,
    url: serverJob.url,
    status: serverJob.status || 'PENDING',
    result: serverJob.result || null,
    meta: null,
    logs: serverJob.result?.logs || [],
    expanded: !finished,
    startedAt,
    finishedAt,
    showAllPosts: false,
  }
  jobs.push(job)
  if (!finished) pollJob(job)
}

onMounted(async () => {
  elapsedInterval = setInterval(() => {
    now.value = Date.now()
  }, 1000)

  if (auth.user) {
    activeTab.value = normalizeTab(route.query.tab)

    const loaders = [loadCookieStatus(), refreshHistory()]
    if (isAdmin.value) loaders.push(fetchScheduledTasks())
    await Promise.all(loaders)

    if (route.query.tab !== activeTab.value) {
      router.replace({
        query: {
          ...route.query,
          tab: activeTab.value,
        },
      })
    }
  }
})

watch(activeTab, (tab) => {
  const nextTab = normalizeTab(tab)
  if (nextTab !== tab) {
    activeTab.value = nextTab
    return
  }

  if (route.query.tab !== nextTab) {
    router.replace({
      query: {
        ...route.query,
        tab: nextTab,
      },
    })
  }
})

onUnmounted(() => {
  Object.values(timers).forEach(clearTimeout)
  if (elapsedInterval) clearInterval(elapsedInterval)
})

async function startImportForUrl(url) {
  const { data } = await api.post('/import', { url })
  const initialStatus = data.queued ? 'QUEUED' : 'PENDING'
  const job = {
    id: data.id,
    url,
    status: initialStatus,
    result: null,
    meta: null,
    logs: [],
    expanded: true,
    startedAt: Date.now(),
    finishedAt: null,
    showAllPosts: false,
  }
  jobs.unshift(job)
  pollJob(job)
}

async function startSingleImport() {
  if (!isLikelyHttpUrl(singleUrl.value.trim())) {
    error.value = 'Enter a valid http/https URL.'
    return
  }
  importingSingle.value = true
  error.value = ''
  try {
    await startImportForUrl(singleUrl.value.trim())
    singleUrl.value = ''
  } catch (err) {
    error.value = err.response?.data?.message || 'Import failed.'
  } finally {
    importingSingle.value = false
  }
}

async function startBatchImport() {
  if (!parsedBatchUrls.value.length) return
  importingBatch.value = true
  error.value = ''
  const failed = []

  for (const url of parsedBatchUrls.value) {
    try {
      await startImportForUrl(url)
    } catch {
      failed.push(url)
    }
  }

  if (failed.length) {
    error.value = `Queued with ${failed.length} error${failed.length !== 1 ? 's' : ''}.`
  }
  batchInput.value = ''
  importingBatch.value = false
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

    if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(data.status)) {
      job.result = data.result
      job.finishedAt = Date.now()
      if (data.result?.logs) job.logs = data.result.logs
      delete timers[job.id]
    } else {
      const delay = ['QUEUED', 'PENDING'].includes(data.status) ? 5000 : 2000
      timers[job.id] = setTimeout(() => pollJob(job), delay)
    }
  } catch {
    job.status = 'ERROR'
    job.finishedAt = Date.now()
    delete timers[job.id]
  }
}

async function stopJob(job) {
  try {
    await api.delete('/import', { params: { id: job.id } })
    job.status = 'REVOKED'
    job.finishedAt = Date.now()
    if (timers[job.id]) {
      clearTimeout(timers[job.id])
      delete timers[job.id]
    }
  } catch {
    error.value = 'Failed to stop import.'
  }
}

async function retryJob(job) {
  if (!job.url) return
  try {
    await startImportForUrl(job.url)
  } catch {
    error.value = 'Failed to retry import.'
  }
}

function dismissJob(id) {
  if (timers[id]) {
    clearTimeout(timers[id])
    delete timers[id]
  }
  const idx = jobs.findIndex(j => j.id === id)
  if (idx !== -1) jobs.splice(idx, 1)
}

function clearFinished() {
  for (let i = jobs.length - 1; i >= 0; i -= 1) {
    if (!isJobActive(jobs[i])) {
      const id = jobs[i].id
      if (timers[id]) {
        clearTimeout(timers[id])
        delete timers[id]
      }
      jobs.splice(i, 1)
    }
  }
}

function openNewScheduledForm() {
  scheduledEditId.value = null
  Object.assign(scheduledForm, { url: '', label: '', interval_minutes: 1440, enabled: true, cookies: '' })
  scheduledFormVisible.value = true
}

function openEditScheduledForm(task) {
  scheduledEditId.value = task.id
  Object.assign(scheduledForm, {
    url: task.url,
    label: task.label || '',
    interval_minutes: task.interval_minutes,
    enabled: task.enabled,
    cookies: '',
  })
  scheduledFormVisible.value = true
}

function cancelScheduledForm() {
  scheduledFormVisible.value = false
}

async function fetchScheduledTasks() {
  scheduledLoading.value = true
  try {
    const { data } = await api.get('/admin/scheduled-imports')
    scheduledTasks.value = data.data || []
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to fetch scheduler tasks.'
  } finally {
    scheduledLoading.value = false
  }
}

async function saveScheduledTask() {
  const payload = {
    url: scheduledForm.url.trim(),
    label: scheduledForm.label.trim() || null,
    interval_minutes: scheduledForm.interval_minutes,
    enabled: scheduledForm.enabled,
    cookies: scheduledForm.cookies.trim() || null,
  }
  if (!payload.url) {
    error.value = 'Scheduler URL is required.'
    return
  }

  try {
    if (scheduledEditId.value !== null) {
      await api.put('/admin/scheduled-imports', { ...payload, id: scheduledEditId.value })
    } else {
      await api.post('/admin/scheduled-imports', payload)
    }
    scheduledFormVisible.value = false
    await fetchScheduledTasks()
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to save scheduled task.'
  }
}

async function deleteScheduledTask(task) {
  if (!confirm(`Delete scheduled task for "${task.url}"?`)) return
  try {
    await api.delete('/admin/scheduled-imports', { data: { id: task.id } })
    await fetchScheduledTasks()
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to delete scheduled task.'
  }
}

async function runScheduledTaskNow(task) {
  try {
    await api.post('/admin/scheduled-imports/run', { id: task.id })
    await fetchScheduledTasks()
    await refreshHistory()
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to run scheduled task.'
  }
}

async function toggleScheduledEnabled(task) {
  try {
    await api.put('/admin/scheduled-imports', { id: task.id, enabled: !task.enabled })
    task.enabled = !task.enabled
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to update scheduler task.'
  }
}

function intervalLabel(minutes) {
  const opt = INTERVAL_OPTIONS.find(o => o.value === minutes)
  return opt ? opt.label : `${minutes} min`
}

function scheduledDotClass(task) {
  if (!task.enabled) return 'task-status-dot-disabled'
  if (task.last_run_status === 'FAILED') return 'task-status-dot-failure'
  if (task.last_run_status === 'QUEUED') return 'task-status-dot-pending'
  return 'task-status-dot-success'
}

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleString() : '-'
}

async function refreshHistory() {
  try {
    const { data } = await api.get('/imports', { params: { mine: 1, per_page: 50 } })
    for (const entry of data.data || []) mergeServerJob(entry)
    jobs.sort((a, b) => b.startedAt - a.startedAt)
  } catch {
    error.value = 'Failed to load import history.'
  }
}

async function loadCookieStatus() {
  try {
    const { data } = await api.get('/profile/cookies')
    hasCookies.value = data.has_cookies
  } catch {
    hasCookies.value = false
  }
}

async function uploadCookies() {
  cookieError.value = ''
  cookieSuccess.value = ''
  if (!cookiePassword.value) {
    cookieError.value = 'Password is required.'
    return
  }

  const file = cookieFileInput.value?.files?.[0]
  if (!file) {
    cookieError.value = 'Select a cookies file.'
    return
  }

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
.import-page {
  width: min(78rem, 100%);
  margin: 0 auto;
}

.import-layout {
  display: grid;
  grid-template-columns: minmax(17rem, 20rem) minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
  isolation: isolate;
}

.import-sidebar {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  align-self: start;
  position: sticky;
  top: 1rem;
  display: grid;
  gap: 0.75rem;
  z-index: 3;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  padding: 0.9rem;
}

.sidebar-title {
  margin: 0;
}

.sidebar-intro {
  margin: 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
  border-radius: 0;
}

.stats-card,
.cookies-card,
.section-card {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  padding: 0.9rem;
}

.stats-card h3,
.cookies-card h3 {
  font-size: 0.92rem;
  margin-bottom: 0.4rem;
}

.stats-grid {
  display: grid;
  gap: 0.35rem;
}

.import-content {
  display: grid;
  gap: 1rem;
  min-width: 0;
  position: relative;
  z-index: 2;
}

.view-tabs {
  display: flex;
  gap: 0.5rem;
}

.tab-btn {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.tab-btn.active {
  color: var(--text);
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 20%, var(--bg-overlay));
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.job-tools {
  display: flex;
  gap: 0.4rem;
  align-items: center;
  flex-wrap: wrap;
}

.admin-inline-input,
.admin-inline-select {
  font: inherit;
  border: 1px solid var(--border);
  background: var(--bg-overlay);
  color: var(--text);
  padding: 0.3em 0.5em;
  font-size: 0.82rem;
}

.single-import-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.batch-area {
  display: grid;
  gap: 0.4rem;
}

.batch-actions {
  display: flex;
  gap: 0.45rem;
  align-items: center;
  flex-wrap: wrap;
}

.batch-area label,
.field label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  font-weight: 600;
}

.field {
  display: grid;
  gap: 0.3rem;
  margin-bottom: 0.65rem;
  min-width: 0;
}

.field:last-of-type {
  margin-bottom: 0;
}

.cookie-file-input {
  display: block;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  font-size: 0.8rem;
  margin-top: 0.35rem;
}

.cookie-file-input::file-selector-button {
  margin-right: 0.55rem;
  border: 1px solid var(--border);
  background: var(--bg-overlay);
  color: var(--text);
  padding: 0.35rem 0.55rem;
  cursor: pointer;
}

.cookies-actions {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.8rem;
  flex-wrap: wrap;
}

.table-wrap {
  overflow-x: auto;
}

.scheduled-table {
  width: 100%;
  table-layout: auto;
}

.scheduled-table th,
.scheduled-table td {
  padding: 0.4rem 0.45rem;
  vertical-align: middle;
}

.scheduled-table th:last-child,
.scheduled-table td:last-child {
  width: 1%;
  white-space: nowrap;
}

.compact-textarea {
  resize: vertical;
  min-height: 2.75rem;
}

.scheduled-form {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  padding: 0.8rem;
  margin-bottom: 0.8rem;
}

.scheduled-form h3 {
  margin-bottom: 0.6rem;
}

.form-row {
  display: grid;
  gap: 0.3rem;
  margin-bottom: 0.6rem;
}

.form-row-inline {
  grid-template-columns: auto auto;
  align-items: center;
  justify-content: start;
  gap: 0.5rem;
}

.form-actions {
  display: flex;
  gap: 0.45rem;
}

.full-width {
  width: 100%;
}

.task-primary {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.55rem;
  align-items: start;
}

.task-actions {
  display: inline-flex;
  gap: 0.3rem;
  flex-wrap: nowrap;
  align-items: center;
}

.task-actions .btn-sm {
  padding: 0.28rem 0.45rem;
  font-size: 0.74rem;
  line-height: 1.15;
  flex: 0 0 auto;
}

.btn-icon {
  min-width: 2rem;
  text-align: center;
  padding: 0.25rem 0.35rem !important;
}

.task-status-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 999px;
  margin-top: 0.32rem;
  flex-shrink: 0;
}

.task-status-dot-success {
  background: #8fdf8f;
}

.task-status-dot-failure {
  background: #df8f8f;
}

.task-status-dot-pending {
  background: #dfcf8f;
}

.task-status-dot-disabled {
  background: var(--text-muted);
  opacity: 0.75;
}

.task-url-text {
  font-size: 0.74rem;
  word-break: break-all;
}

.task-disabled {
  opacity: 0.72;
}

.job-list {
  display: grid;
  gap: 0.6rem;
}

.import-job {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  overflow: hidden;
}

.job-header {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: center;
  padding: 0.6rem 0.7rem;
  cursor: pointer;
}

.job-header:hover {
  background: var(--item-hover);
}

.job-meta {
  display: grid;
  gap: 0.25rem;
  justify-items: start;
  min-width: 3.6rem;
}

.job-main {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.job-url {
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.job-subtitle {
  font-size: 0.76rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.job-elapsed {
  font-size: 0.74rem;
  font-variant-numeric: tabular-nums;
}

.job-actions {
  display: flex;
  gap: 0.3rem;
}

.job-body {
  padding: 0 0.75rem 0.75rem;
}

.progress-bar {
  position: relative;
  height: 1.3rem;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  margin-bottom: 0.75rem;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.25s ease;
}

.progress-label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.74rem;
  font-weight: 600;
}

.import-logs {
  margin-bottom: 0.75rem;
}

.log-output {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  padding: 0.6rem;
  font-size: 0.77rem;
  max-height: 16rem;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.import-count {
  margin-bottom: 0.6rem;
}

.collection-badge {
  color: var(--text-muted);
}

.import-posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(8.8rem, 1fr));
  gap: 0.5rem;
}

.import-posts-grid .post-thumb {
  display: block;
  height: 8.8rem;
  overflow: hidden;
}

.import-posts-grid :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.show-more-btn {
  margin-top: 0.45rem;
  width: 100%;
  border: 1px solid var(--border);
  background: var(--bg-overlay);
  color: var(--text-muted);
}

.show-more-btn:hover {
  background: var(--item-hover);
}

.error-list {
  margin-top: 0.55rem;
  display: grid;
  gap: 0.25rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-success {
  background: #8fdf8f;
}

.dot-failure {
  background: #df8f8f;
}

.dot-pending {
  background: #dfcf8f;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}

.status-badge {
  padding: 0.15em 0.5em;
  border-radius: var(--radius-xs);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
}

.stats-grid .status-badge {
  display: block;
  width: 100%;
  text-align: left;
  box-sizing: border-box;
}

.status-success {
  background: #2d5a2d;
  color: #8fdf8f;
}

.status-failure {
  background: #5a2d2d;
  color: #df8f8f;
}

.status-pending {
  background: #5a4d2d;
  color: #dfcf8f;
}

@media (max-width: 1020px) {
  .import-layout {
    grid-template-columns: 1fr;
  }

  .import-sidebar {
    position: static;
  }

  .section-head {
    flex-direction: column;
    align-items: stretch;
  }

  .single-import-row {
    grid-template-columns: 1fr;
  }

  .job-header {
    grid-template-columns: auto 1fr auto;
    align-items: start;
  }

  .job-meta {
    order: 3;
    grid-auto-flow: column;
    align-items: center;
    min-width: 0;
  }

  .job-main {
    order: 2;
  }

  .job-actions {
    order: 4;
  }

  .scheduled-table {
    table-layout: auto;
  }

  .table-wrap {
    overflow-x: auto;
  }
}
</style>
