<template>
  <div class="page-container admin-page">
    <div class="admin-layout">

      <!-- Sidebar -->
      <nav class="admin-sidebar">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="sidebar-item"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="sidebar-icon">{{ tab.icon }}</span>
          <span class="sidebar-label">{{ tab.label }}</span>
        </button>
      </nav>

      <!-- Main content -->
      <div class="admin-content">

        <!-- Stats -->
        <section v-show="activeTab === 'stats'" class="admin-section">
          <h2>Site Statistics</h2>
          <div v-if="stats" class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ stats.posts }}</span>
              <span class="stat-label">Posts</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ stats.users }}</span>
              <span class="stat-label">Users</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ stats.tags }}</span>
              <span class="stat-label">Tags</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ stats.collections }}</span>
              <span class="stat-label">Collections</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ stats.errors }}</span>
              <span class="stat-label">Errors</span>
            </div>
          </div>
          <p v-else class="text-muted">Loading stats...</p>
        </section>

        <!-- Import Jobs -->
        <section v-show="activeTab === 'imports'" class="admin-section">
          <div class="section-header">
            <h2>Import Jobs</h2>
            <button class="btn-sm" @click="refreshImports" title="Refresh">↻</button>
          </div>

          <div v-if="importJobs.length" class="import-list">
            <div v-for="job in importJobs" :key="job.id" class="import-job">
              <div class="job-header" @click="job.expanded = !job.expanded">
                <span class="status-dot" :class="dotClass(job)"></span>
                <span class="job-url">{{ job.url || job.id }}</span>
                <span v-if="job.user" class="job-user text-muted" title="Submitted by">@{{ job.user.username }}</span>
                <span class="job-elapsed text-muted">{{ elapsed(job) }}</span>
                <span class="status-badge" :class="badgeClass(job)">{{ displayStatus(job) }}</span>
                <button
                  v-if="isJobActive(job)"
                  class="btn-sm danger job-action"
                  title="Stop task"
                  @click.stop="stopJob(job)"
                >■ Stop</button>
              </div>
              <div v-if="job.expanded" class="job-body">
                <div v-if="job.meta && job.meta.total" class="progress-bar">
                  <div class="progress-fill" :style="{ width: (job.meta.current / job.meta.total * 100) + '%' }"></div>
                  <span class="progress-label">{{ job.meta.current }} / {{ job.meta.total }}</span>
                </div>
                <div v-if="job.logs.length" class="import-logs">
                  <pre class="log-output log-box">{{ joinLines(job.logs) }}</pre>
                </div>
                <p v-else class="text-muted" style="font-size:0.85rem">Waiting for logs...</p>
                <template v-if="job.result && job.result.posts">
                  <p class="import-count">Imported {{ job.result.count }} post{{ job.result.count !== 1 ? 's' : '' }}</p>
                </template>
                <p v-if="job.result && job.result.error" class="text-error">{{ job.result.error }}</p>
              </div>
            </div>
          </div>
          <p v-else class="text-muted">No import jobs.</p>

          <!-- Import pagination (server-driven) -->
          <div v-if="importTotalPages > 1" class="import-pagination">
            <button class="btn-sm" :disabled="importPage <= 1" @click="importPage--; refreshImports()">‹</button>
            <span class="text-muted">{{ importPage }} / {{ importTotalPages }}</span>
            <button class="btn-sm" :disabled="importPage >= importTotalPages" @click="importPage++; refreshImports()">›</button>
          </div>
        </section>

        <!-- User Management -->
        <section v-show="activeTab === 'users'" class="admin-section">
          <h2>User Management</h2>

          <details class="create-user-details" v-if="auth.user?.role >= 300">
            <summary class="btn-sm" style="display:inline-block;margin-bottom:0.75em;cursor:pointer">+ Create User</summary>
            <form class="create-user-form" @submit.prevent="createUser">
              <input v-model="newUser.username" placeholder="Username" required />
              <input v-model="newUser.email" placeholder="Email (optional)" type="email" />
              <input v-model="newUser.password" placeholder="Password" type="password" required />
              <select v-model="newUser.role">
                <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
              </select>
              <button type="submit" :disabled="creatingUser">{{ creatingUser ? 'Creating…' : 'Create' }}</button>
            </form>
            <p v-if="createUserMsg" :class="createUserError ? 'text-error' : 'text-success'">{{ createUserMsg }}</p>
          </details>

          <div class="user-search-bar">
            <input v-model="userSearch" placeholder="Search by username..." @keyup.enter="fetchUsers" />
            <button class="btn-sm" @click="fetchUsers">Search</button>
          </div>
          <table v-if="users.length">
            <thead>
              <tr><th>ID</th><th>Username</th><th>Role</th><th>Posts</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td>{{ u.id }}</td>
                <td>
                  <router-link :to="`/users/${u.id}`">{{ u.username }}</router-link>
                </td>
                <td>
                  <select v-if="auth.user?.role >= 300" v-model="u._pendingRole" @change="changeRole(u)" class="role-select">
                    <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
                  </select>
                  <span v-else>{{ roleName(u.role) }}</span>
                </td>
                <td>{{ u.post_count }}</td>
                <td>
                  <router-link v-if="auth.user?.role >= 300" :to="`/admin/users/${u.id}/edit`" class="btn-sm">Edit</router-link>
                  <button v-if="auth.user?.role >= 300 && u.id !== auth.user?.id" class="btn-sm danger" @click="deleteUser(u.id)">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="text-muted">No users found.</p>
        </section>

        <!-- Tasks -->
        <section v-show="activeTab === 'tasks'" class="admin-section">
          <h2>Run Tasks</h2>
          <div class="task-list">
            <div class="task-item">
              <div>
                <strong>Remove Expired Bans</strong>
                <p class="text-muted">Clear all bans that have passed their expiry date.</p>
              </div>
              <button @click="runTask('remove_expired_bans')" :disabled="!!runningTask">
                {{ runningTask === 'remove_expired_bans' ? 'Running...' : 'Run' }}
              </button>
            </div>
            <div class="task-item">
              <div>
                <strong>Backfill Video Thumbnails</strong>
                <p class="text-muted">Generate missing JPEG thumbnails for all video posts.</p>
              </div>
              <button @click="runTask('backfill_video_thumbnails')" :disabled="!!runningTask">
                {{ runningTask === 'backfill_video_thumbnails' ? 'Running...' : 'Run' }}
              </button>
            </div>
            <div class="task-item">
              <div>
                <strong>Recount Tag Post Counts</strong>
                <p class="text-muted">Recalculate post_count for every tag from scratch.</p>
              </div>
              <button @click="runTask('recount_tags')" :disabled="!!runningTask">
                {{ runningTask === 'recount_tags' ? 'Running...' : 'Run' }}
              </button>
            </div>
            <div class="task-item">
              <div>
                <strong>Migrate Images (shard layout)</strong>
                <p class="text-muted">Move flat-directory images into the two-level sharded layout. Safe to re-run.</p>
              </div>
              <button @click="runTask('migrate_images')" :disabled="!!runningTask">
                {{ runningTask === 'migrate_images' ? 'Running...' : 'Run' }}
              </button>
            </div>
            <div class="task-item">
              <div>
                <strong>Clear Import Queue</strong>
                <p class="text-muted">Cancel all queued (not yet started) import jobs.</p>
              </div>
              <button @click="runTask('clear_import_queue')" :disabled="!!runningTask">
                {{ runningTask === 'clear_import_queue' ? 'Running...' : 'Run' }}
              </button>
            </div>
            <div class="task-item">
              <div>
                <strong>Restart Celery Worker Pool</strong>
                <p class="text-muted">Hot-restart worker processes without stopping the queue (pool_restart broadcast).</p>
              </div>
              <button @click="runTask('restart_celery')" :disabled="!!runningTask">
                {{ runningTask === 'restart_celery' ? 'Restarting...' : 'Restart' }}
              </button>
            </div>
          </div>
          <p v-if="taskMessage" :class="taskError ? 'text-error' : 'text-success'">{{ taskMessage }}</p>
        </section>

        <!-- Error Log -->
        <section v-show="activeTab === 'errors'" class="admin-section">
          <h2>Recent Errors</h2>
          <table v-if="errors.length" class="errors-table">
            <thead><tr><th>Type</th><th>Date</th><th></th></tr></thead>
            <tbody>
              <template v-for="err in errors" :key="err.id">
                <tr class="error-row" @click="toggleError(err.id)">
                  <td>{{ err.exception_type }}</td>
                  <td>{{ formatDate(err.created_at) }}</td>
                  <td class="expand-col">{{ expandedErrors.has(err.id) ? '▲' : '▼' }}</td>
                </tr>
                <tr v-if="expandedErrors.has(err.id)" class="error-traceback-row">
                  <td colspan="3">
                    <pre class="traceback-box">{{ err.traceback || 'No traceback available.' }}</pre>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
          <p v-else class="text-muted">No errors logged.</p>
        </section>

        <!-- Scheduled Imports -->
        <section v-show="activeTab === 'scheduled'" class="admin-section">
          <div class="section-header">
            <h2>Scheduled Imports</h2>
            <button class="btn-sm" @click="openNewScheduledForm">+ New</button>
          </div>

          <!-- Create / Edit form -->
          <div v-if="scheduledFormVisible" class="scheduled-form">
            <h3>{{ scheduledEditId !== null ? 'Edit Task' : 'New Scheduled Task' }}</h3>
            <div class="form-row">
              <label>URL</label>
              <input v-model="scheduledForm.url" type="url" placeholder="https://example.com/gallery" class="full-width" />
            </div>
            <div class="form-row">
              <label>Label <span class="text-muted">(optional)</span></label>
              <input v-model="scheduledForm.label" type="text" placeholder="e.g. Artist gallery" class="full-width" />
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
              <label>Cookies <span class="text-muted">(Netscape/header format — leave blank to keep existing)</span></label>
              <textarea v-model="scheduledForm.cookies" rows="4" class="full-width cookie-textarea" placeholder="# Netscape HTTP Cookie File&#10;..."></textarea>
            </div>
            <div class="form-actions">
              <button @click="saveScheduledTask" class="btn-primary">{{ scheduledEditId !== null ? 'Save' : 'Create' }}</button>
              <button @click="cancelScheduledForm" class="btn-sm">Cancel</button>
            </div>
          </div>

          <p v-if="scheduledLoading && !scheduledTasks.length" class="text-muted">Loading…</p>
          <p v-else-if="!scheduledTasks.length && !scheduledFormVisible" class="text-muted">No scheduled tasks yet.</p>

          <table v-if="scheduledTasks.length" class="scheduled-table">
            <thead>
              <tr>
                <th>Label / URL</th>
                <th>Interval</th>
                <th>Last Run</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in scheduledTasks" :key="task.id" :class="{ 'task-disabled': !task.enabled }">
                <td class="task-url-cell">
                  <span v-if="task.label" class="task-label">{{ task.label }}</span>
                  <span class="task-url">{{ task.url }}</span>
                  <span v-if="task.has_cookies" class="cookie-badge" title="Has cookies stored">🍪</span>
                </td>
                <td>{{ intervalLabel(task.interval_minutes) }}</td>
                <td class="text-muted">{{ task.last_run_at ? formatDate(task.last_run_at) : 'Never' }}</td>
                <td>
                  <span v-if="task.last_run_status" :class="['status-badge', scheduledStatusClass(task.last_run_status)]">
                    {{ task.last_run_status }}
                  </span>
                  <span v-else class="text-muted">—</span>
                </td>
                <td class="task-actions">
                  <button class="btn-sm" @click="openEditScheduledForm(task)">Edit</button>
                  <button class="btn-sm" @click="runScheduledTaskNow(task)" title="Dispatch now, ignoring interval">Run now</button>
                  <button class="btn-sm danger" @click="deleteScheduledTask(task)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Logs (Celery + Flask access/error) -->
        <section v-show="activeTab === 'logs'" class="admin-section">
          <div class="section-header">
            <h2>Logs</h2>
            <span class="log-controls">
              <select v-model="logsLines" @change="fetchActiveLog" class="lines-select">
                <option :value="50">Last 50</option>
                <option :value="100">Last 100</option>
                <option :value="200">Last 200</option>
                <option :value="500">Last 500</option>
              </select>
              <button class="btn-sm" @click="fetchActiveLog" :disabled="logsLoading">↻</button>
            </span>
          </div>

          <!-- Horizontal log sub-tabs -->
          <div class="log-tabs">
            <button
              v-for="lt in logTypes"
              :key="lt.id"
              class="log-tab-btn"
              :class="{ active: activeLogType === lt.id }"
              @click="switchLogType(lt.id)"
            >{{ lt.label }}</button>
          </div>

          <template v-if="logsData.available">
            <div ref="logBoxEl" class="log-output log-box log-box-tall">
              <div v-for="(line, i) in logsData.lines" :key="i" :class="logLineClass(line)">{{ line }}</div>
            </div>
          </template>
          <p v-else-if="logsLoading" class="text-muted">Loading…</p>
          <p v-else class="text-muted">Log file not yet available.</p>
        </section>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()

const auth = useAuthStore()
const stats = ref(null)
const errors = ref([])
const expandedErrors = ref(new Set())
const runningTask = ref(null)
const taskMessage = ref('')
const taskError = ref(false)
const importJobs = reactive([])
const users = ref([])
const userSearch = ref('')
const now = ref(Date.now())
const pollTimers = {}
let refreshTimer = null
let clockTimer = null

// Scheduled imports state
const scheduledTasks = ref([])
const scheduledLoading = ref(false)
const scheduledFormVisible = ref(false)
const scheduledEditId = ref(null)
const INTERVAL_OPTIONS = [
  { value: 30,    label: '30 minutes' },
  { value: 60,    label: '1 hour' },
  { value: 120,   label: '2 hours' },
  { value: 360,   label: '6 hours' },
  { value: 720,   label: '12 hours' },
  { value: 1440,  label: 'Daily (24h)' },
  { value: 2880,  label: 'Every 2 days' },
  { value: 10080, label: 'Weekly' },
]
const scheduledForm = reactive({
  url: '', label: '', interval_minutes: 1440, enabled: true, cookies: '',
})

const celeryLogs = ref([])
const celeryLogsAvailable = ref(false)
const celeryLogsLoading = ref(false)
const celeryLogsLines = ref(100)
const celeryLogEl = ref(null)

// Unified log viewer state
const logTypes = [
  { id: 'celery',  label: 'Celery' },
  { id: 'access',  label: 'Access' },
  { id: 'error',   label: 'Error' },
]
const activeLogType = ref('celery')
const logsLines = ref(100)
const logsLoading = ref(false)
const logsData = ref({ lines: [], available: false })
const logBoxEl = ref(null)

const newUser = reactive({ username: '', email: '', password: '', role: 'MEMBER' })
const creatingUser = ref(false)
const createUserMsg = ref('')
const createUserError = ref(false)

// Sidebar tabs — restore from ?tab= query param if present
const VALID_TABS = new Set(['stats','imports','scheduled','users','tasks','errors','logs'])
const activeTab = ref(VALID_TABS.has(route.query.tab) ? route.query.tab : 'stats')
const tabs = [
  { id: 'stats',     icon: '📊', label: 'Statistics' },
  { id: 'imports',   icon: '📥', label: 'Imports' },
  { id: 'scheduled', icon: '🕐', label: 'Scheduled' },
  { id: 'users',     icon: '👥', label: 'Users' },
  { id: 'tasks',     icon: '🔧', label: 'Tasks' },
  { id: 'errors',    icon: '🟠', label: 'Errors' },
  { id: 'logs',      icon: '📋', label: 'Logs' },
]

// Import pagination (server-driven)
const importPage = ref(1)
const importPerPage = 20
const importTotalPages = ref(1)

const ROLE_VALUES = { 0: 'MEMBER', 100: 'HELPER', 200: 'MODERATOR', 300: 'ADMIN', 666: 'OWNER' }
const roles = ['MEMBER', 'HELPER', 'MODERATOR', 'ADMIN', 'OWNER']

function roleName(val) { return ROLE_VALUES[val] || val }
function joinLines(arr) { return arr.join('\n') }

function toggleError(id) {
  const s = new Set(expandedErrors.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  expandedErrors.value = s
}

// ── Scheduled imports ───────────────────────────────────────
async function fetchScheduledTasks() {
  scheduledLoading.value = true
  try {
    const { data } = await api.get('/admin/scheduled-imports')
    scheduledTasks.value = data.data
  } catch (err) {
    console.error('Scheduled imports fetch failed:', err)
  } finally {
    scheduledLoading.value = false
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
    cookies: '',   // never pre-fill cookies from server
  })
  scheduledFormVisible.value = true
}

function cancelScheduledForm() {
  scheduledFormVisible.value = false
}

async function saveScheduledTask() {
  const payload = {
    url: scheduledForm.url.trim(),
    label: scheduledForm.label.trim() || null,
    interval_minutes: scheduledForm.interval_minutes,
    enabled: scheduledForm.enabled,
    cookies: scheduledForm.cookies.trim() || null,
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
    console.error('Save scheduled task failed:', err)
  }
}

async function deleteScheduledTask(task) {
  if (!confirm(`Delete scheduled task for "${task.url}"?`)) return
  try {
    await api.delete('/admin/scheduled-imports', { data: { id: task.id } })
    await fetchScheduledTasks()
  } catch (err) {
    console.error('Delete scheduled task failed:', err)
  }
}

async function runScheduledTaskNow(task) {
  try {
    await api.post('/admin/scheduled-imports/run', { id: task.id })
    await fetchScheduledTasks()
  } catch (err) {
    console.error('Run scheduled task failed:', err)
  }
}

function intervalLabel(minutes) {
  const opt = INTERVAL_OPTIONS.find(o => o.value === minutes)
  return opt ? opt.label : `${minutes} min`
}

function scheduledStatusClass(status) {
  if (status === 'DISPATCHED') return 'status-success'
  if (status === 'FAILED') return 'status-failure'
  return 'status-pending'
}
// ────────────────────────────────────────────────────────────

function logLineClass(line) {
  // Celery log: "[timestamp: LEVEL/process] message"
  const celery = line.match(/:\s+(ERROR|CRITICAL|WARNING|INFO|DEBUG)\//)
  if (celery) {
    const lvl = celery[1]
    if (lvl === 'ERROR' || lvl === 'CRITICAL') return 'log-error'
    if (lvl === 'WARNING') return 'log-warn'
    if (lvl === 'DEBUG') return 'log-debug'
    return ''
  }
  // Nginx error log: "date [level] pid: message"
  if (/\[(error|crit|alert|emerg)\]/.test(line)) return 'log-error'
  if (/\[warn\]/.test(line)) return 'log-warn'
  // Combined access log: ip - - [date] "VERB path HTTP/x.x" STATUS bytes
  const acc = line.match(/"[A-Z]+ [^\s]+ HTTP\/[\d.]+"\s+(\d{3})/)
  if (acc) {
    const s = parseInt(acc[1])
    if (s >= 500) return 'log-error'
    if (s >= 400) return 'log-warn'
    if (s >= 200) return 'log-ok'
  }
  return ''
}

function isJobActive(job) {
  return !['SUCCESS', 'FAILURE', 'ERROR', 'REVOKED'].includes(job.status)
}

function jobFailed(job) {
  return job.status === 'FAILURE' || job.status === 'ERROR' || job.status === 'REVOKED' || (job.status === 'SUCCESS' && !!job.result?.error)
}
function jobSucceeded(job) {
  return job.status === 'SUCCESS' && !job.result?.error
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
  if (jobFailed(job)) return job.status === 'REVOKED' ? 'STOPPED' : 'FAILED'
  if (job.status === 'PROGRESS' && job.meta) return `${job.meta.current}/${job.meta.total}`
  return job.status
}

function elapsed(job) {
  if (!job.startedAt) return ''
  const ms = (job.finishedAt || now.value) - job.startedAt
  const secs = Math.floor(ms / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  return `${mins}m ${secs % 60}s`
}

async function stopJob(job) {
  if (!confirm('Stop this import task?')) return
  try {
    await api.delete('/import', { params: { id: job.id } })
  } catch { /* ignore */ }
  job.status = 'REVOKED'
  job.finishedAt = Date.now()
  if (pollTimers[job.id]) { clearTimeout(pollTimers[job.id]); delete pollTimers[job.id] }
}

onMounted(async () => {
  clockTimer = setInterval(() => { now.value = Date.now() }, 1000)

  try {
    const { data } = await api.get('/admin/stats')
    stats.value = data
  } catch (err) {
    if (err.response?.status !== 403) console.error('Admin stats error:', err)
  }
  try {
    const { data } = await api.get('/admin/errors', { params: { per_page: 10 } })
    errors.value = data.data
  } catch (err) {
    console.error('Admin errors fetch failed:', err)
  }
  fetchCeleryLogs()
  fetchActiveLog()
  fetchUsers()
  fetchScheduledTasks()
  refreshImports()
  refreshTimer = setInterval(refreshImports, 10000)
})

onUnmounted(() => {
  Object.values(pollTimers).forEach(clearTimeout)
  if (refreshTimer) clearInterval(refreshTimer)
  if (clockTimer) clearInterval(clockTimer)
})

async function refreshImports() {
  try {
    const { data } = await api.get('/imports', { params: { page: importPage.value, per_page: importPerPage } })
    importTotalPages.value = data.pages || 1

    const incoming = data.data
    const incomingIds = new Set(incoming.map(s => s.id))

    // Remove jobs no longer on this page
    for (let i = importJobs.length - 1; i >= 0; i--) {
      if (!incomingIds.has(importJobs[i].id)) {
        if (pollTimers[importJobs[i].id]) {
          clearTimeout(pollTimers[importJobs[i].id])
          delete pollTimers[importJobs[i].id]
        }
        importJobs.splice(i, 1)
      }
    }

    for (const s of incoming) {
      const finished = ['SUCCESS', 'FAILURE', 'REVOKED', 'ERROR'].includes(s.status)
      const existing = importJobs.find(j => j.id === s.id)

      if (existing) {
        // Only overwrite fields controlled by the server.
        // Preserve live logs/meta from pollJob so they don't flicker.
        existing.user = s.user || null
        existing.url = s.url
        if (finished) {
          existing.status = s.status
          existing.result = s.result || null
          existing.finishedAt = s.finished_at ? new Date(s.finished_at).getTime() : (existing.finishedAt || Date.now())
          if (s.result?.logs?.length) existing.logs = s.result.logs
          if (pollTimers[existing.id]) { clearTimeout(pollTimers[existing.id]); delete pollTimers[existing.id] }
        }
        // If not finished and not already polling, kick off a poll
        if (!finished && !pollTimers[existing.id]) pollJob(existing)
      } else {
        const startedAt = s.created_at ? new Date(s.created_at).getTime() : Date.now()
        const finishedAt = s.finished_at ? new Date(s.finished_at).getTime() : null
        const job = {
          id: s.id,
          url: s.url,
          user: s.user || null,
          status: s.status || 'PENDING',
          result: s.result || null,
          meta: null,
          logs: s.result?.logs || [],
          expanded: false,
          startedAt,
          finishedAt,
        }
        importJobs.push(job)
        if (!finished) pollJob(job)
      }
    }
  } catch (err) {
    if (err.response?.status !== 403) console.error('refreshImports failed:', err)
  }
}

async function pollJob(job) {
  if (pollTimers[job.id]) clearTimeout(pollTimers[job.id])
  try {
    const { data } = await api.get('/import', { params: { id: job.id } })
    job.status = data.status
    if (data.meta) {
      job.meta = data.meta
      if (data.meta.logs) job.logs = data.meta.logs
    }
    if (data.status === 'SUCCESS' || data.status === 'FAILURE' || data.status === 'REVOKED') {
      job.result = data.result
      job.finishedAt = Date.now()
      if (data.result?.logs) job.logs = data.result.logs
      delete pollTimers[job.id]
    } else {
      // Slow-poll for QUEUED/PENDING, faster for active PROGRESS
      const delay = (data.status === 'QUEUED' || data.status === 'PENDING') ? 5000 : 2000
      pollTimers[job.id] = setTimeout(() => pollJob(job), delay)
    }
  } catch {
    job.status = 'ERROR'
    job.finishedAt = Date.now()
    delete pollTimers[job.id]
  }
}

async function fetchUsers() {
  try {
    const { data } = await api.get('/admin/users', { params: { q: userSearch.value || undefined, per_page: 20 } })
    users.value = data.data.map(u => ({ ...u, _pendingRole: roleName(u.role) }))
  } catch { /* ignore */ }
}

async function createUser() {
  creatingUser.value = true
  createUserMsg.value = ''
  createUserError.value = false
  try {
    await api.post('/admin/users', { ...newUser })
    createUserMsg.value = `User '${newUser.username}' created.`
    newUser.username = ''
    newUser.email = ''
    newUser.password = ''
    newUser.role = 'MEMBER'
    fetchUsers()
  } catch (err) {
    createUserMsg.value = err.response?.data?.message || 'Create failed.'
    createUserError.value = true
  } finally {
    creatingUser.value = false
  }
}

async function changeRole(u) {
  try {
    const { data } = await api.put('/admin/users', { id: u.id, role: u._pendingRole })
    u.role = data.role
  } catch (err) {
    alert(err.response?.data?.message || 'Role change failed.')
    u._pendingRole = roleName(u.role)
  }
}

async function deleteUser(id) {
  if (!confirm('Delete this user? This cannot be undone.')) return
  try {
    await api.delete('/admin/users', { data: { id } })
    users.value = users.value.filter(u => u.id !== id)
  } catch (err) {
    alert(err.response?.data?.message || 'Delete failed.')
  }
}

async function runTask(name) {
  runningTask.value = name
  taskMessage.value = ''
  taskError.value = false
  try {
    const { data } = await api.post('/admin/tasks', { task: name })
    taskMessage.value = data.message
  } catch (err) {
    taskMessage.value = err.response?.data?.message || 'Task failed.'
    taskError.value = true
  } finally {
    runningTask.value = null
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

async function fetchCeleryLogs() {
  celeryLogsLoading.value = true
  try {
    const { data } = await api.get('/admin/celery-logs', { params: { lines: celeryLogsLines.value } })
    celeryLogsAvailable.value = data.available
    celeryLogs.value = data.lines || []
  } catch { /* ignore */ } finally {
    celeryLogsLoading.value = false
  }
}

async function fetchActiveLog() {
  logsLoading.value = true
  try {
    let data
    if (activeLogType.value === 'celery') {
      ;({ data } = await api.get('/admin/celery-logs', { params: { lines: logsLines.value } }))
    } else {
      ;({ data } = await api.get('/admin/flask-logs', { params: { type: activeLogType.value, lines: logsLines.value } }))
    }
    logsData.value = { lines: data.lines || [], available: data.available }
    await nextTick()
    if (logBoxEl.value) logBoxEl.value.scrollTop = logBoxEl.value.scrollHeight
  } catch { /* ignore */ } finally {
    logsLoading.value = false
  }
}

function switchLogType(type) {
  activeLogType.value = type
  logsData.value = { lines: [], available: false }
  fetchActiveLog()
}
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────── */
.admin-page {
  padding: 0 !important; /* override page-container; sidebar border must touch edges */
}
.admin-layout {
  display: flex;
  gap: 0;
  min-height: 60vh;
}

/* ── Sidebar ─────────────────────────────────────────────── */
.admin-sidebar {
  display: flex;
  flex-direction: column;
  width: 11em;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  padding-top: 1.5em;
  background: var(--bg-overlay);
}
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 0.5em;
  background: none;
  border: none;
  padding: 0.65em 1em;
  text-align: left;
  cursor: pointer;
  color: var(--text);
  font-size: 0.9rem;
  border-left: 3px solid transparent;
  transition: background 0.1s, border-color 0.1s;
}
.sidebar-item:hover { background: var(--item-hover); }
.sidebar-item.active {
  background: var(--item-hover);
  border-left-color: var(--accent, #5a8a5a);
  font-weight: 600;
}
.sidebar-icon { font-size: 1rem; flex-shrink: 0; }
.sidebar-label { white-space: nowrap; }

/* ── Content pane ─────────────────────────────────────────── */
.admin-content {
  flex: 1;
  min-width: 0;
  padding: 1.5em 1.5em 1.5em 1.5em;
}
.admin-section h2 {
  margin: 0 0 1em 0;
  padding-top: 0.1em;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 0.75em;
  margin-bottom: 1em;
}
.section-header h2 { margin: 0; }

/* ── Import jobs ──────────────────────────────────────────── */
.import-list { display: flex; flex-direction: column; gap: 0.5em; }
.import-job {
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
.job-user {
  font-size: 0.75rem;
  flex-shrink: 0;
  max-width: 8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.job-elapsed {
  font-size: 0.75rem;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.job-action { flex-shrink: 0; margin-left: 0.25em; }
.job-body { padding: 0 0.75rem 0.75rem; }

.import-pagination {
  display: flex;
  align-items: center;
  gap: 0.75em;
  margin-top: 0.75em;
  font-size: 0.85rem;
}

/* ── Progress bar ─────────────────────────────────────────── */
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
.import-count {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0;
}

/* ── Log sub-tabs ─────────────────────────────────────────── */
.log-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.75em;
}
.log-tab-btn {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 0.4em 1em;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-bottom: -1px;
  transition: color 0.1s, border-color 0.1s;
}
.log-tab-btn:hover { color: var(--text); }
.log-tab-btn.active {
  color: var(--text);
  border-bottom-color: var(--accent, #5a8a5a);
  font-weight: 600;
}
.log-box-tall { max-height: 52rem; font-size: 0.75rem; line-height: 1.4; }

/* Log line colours */
.log-error   { color: #df8f8f; }
.log-warn    { color: #dfcf8f; }
.log-ok      { color: #8fdf9f; }
.log-debug   { color: #7c7c7c; }

/* ── Log box ──────────────────────────────────────────────── */
.log-output {
  font-size: 0.8rem;
  max-height: 14rem;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  border-radius: 4px;
  padding: 0.5rem;
}
.log-box {
  background: #0d0d0d;
  border: 1px solid var(--border);
  color: #c8c8c8;
}
.celery-log-output {
  max-height: 28rem;
  font-size: 0.75rem;
  line-height: 1.4;
}
.log-controls {
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  font-size: 0.85rem;
  font-weight: 400;
}
.lines-select {
  background: var(--bg-overlay);
  color: var(--text);
  border: none;
  padding: 2px 6px;
  font-size: 0.8rem;
  border-radius: 4px;
}

/* ── Stats ────────────────────────────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(8em, 1fr));
  gap: 1em;
}
.stat-card {
  background-color: var(--bg-overlay);
  padding: 1em;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25em;
}
.stat-value { font-size: 2rem; font-weight: 700; }
.stat-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── Errors ───────────────────────────────────────────────── */
.errors-table { width: 100%; }
.error-row { cursor: pointer; }
.error-row:hover { background: var(--bg-overlay); }
.expand-col { width: 2em; text-align: center; color: var(--text-muted); }
.traceback-box {
  font-size: 0.72rem;
  white-space: pre-wrap;
  word-break: break-all;
  padding: 0.5rem;
  background: #0d0d0d;
  border: 1px solid var(--border);
  color: #c8c8c8;
  margin: 0.25rem 0;
  border-radius: 4px;
  max-height: 20rem;
  overflow-y: auto;
}

/* ── Scheduled imports ────────────────────────────────────── */
.scheduled-form {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1em;
  margin-bottom: 1em;
}
.scheduled-form h3 { margin: 0 0 0.75em; font-size: 0.95rem; }
.form-row         { display: flex; flex-direction: column; gap: 0.25em; margin-bottom: 0.6em; }
.form-row label   { font-size: 0.8rem; color: var(--text-muted); }
.form-row-inline  { flex-direction: row; align-items: center; gap: 0.5em; }
.full-width       { width: 100%; box-sizing: border-box; }
.cookie-textarea  { font-family: monospace; font-size: 0.75rem; resize: vertical; }
.form-actions     { display: flex; gap: 0.5em; margin-top: 0.75em; }
.btn-primary      { background: var(--accent, #5a8a5a); color: #fff; border: none; padding: 0.35em 0.9em; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
.btn-primary:hover { filter: brightness(1.15); }
.scheduled-table  { width: 100%; }
.scheduled-table th { font-size: 0.78rem; color: var(--text-muted); font-weight: 600; padding-bottom: 0.3em; }
.task-url-cell    { max-width: 28em; }
.task-label       { display: block; font-weight: 600; font-size: 0.85rem; }
.task-url         { display: block; font-size: 0.75rem; color: var(--text-muted); word-break: break-all; }
.task-disabled    { opacity: 0.5; }
.cookie-badge     { font-size: 0.75rem; margin-left: 0.3em; }
.task-actions     { white-space: nowrap; }
.task-actions button { margin-left: 0.25em; }

/* ── Users ────────────────────────────────────────────────── */
.user-search-bar { display: flex; gap: 0.5em; margin-bottom: 0.75em; }
.user-search-bar input { flex: 1; }
.create-user-details { margin-bottom: 0.75em; }
.create-user-details summary { list-style: none; }
.create-user-details summary::-webkit-details-marker { display: none; }
.create-user-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em;
  margin-top: 0.75em;
  margin-bottom: 0.5em;
}
.create-user-form input,
.create-user-form select { flex: 1; min-width: 10em; }
.create-user-form button { flex-shrink: 0; }
.role-select {
  background: var(--bg-overlay);
  color: var(--text);
  border: none;
  padding: 2px 4px;
  font-size: 0.85rem;
}

/* ── Tasks ────────────────────────────────────────────────── */
.task-list { display: flex; flex-direction: column; gap: 0.75em; }
.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--bg-overlay);
  padding: 1em;
  gap: 1em;
}
.task-item p { font-size: 0.85rem; margin: 0; }

/* ── Badges ───────────────────────────────────────────────── */
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

/* ── Buttons ──────────────────────────────────────────────── */
.btn-sm {
  font: inherit;
  cursor: pointer;
  border: none;
  padding: 4px 10px;
  font-size: 0.85rem;
  background: var(--bg-raised);
  color: var(--text);
  border-radius: 4px;
}
.btn-sm:hover { background: var(--item-hover); }
.btn-sm.danger { color: #df8f8f; }
.btn-sm.danger:hover { background: #5a2d2d; }

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 689px) {
  .admin-layout { flex-direction: column; }
  .admin-sidebar {
    flex-direction: row;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    padding: 0;
  }  .sidebar-item {
    border-left: none;
    border-bottom: 3px solid transparent;
    padding: 0.5em 0.75em;
    flex-direction: column;
    gap: 0.15em;
    font-size: 0.75rem;
  }
  .sidebar-item.active { border-bottom-color: var(--accent, #5a8a5a); border-left-color: transparent; }
  .admin-content { padding: 0.75em 0 0 0; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
