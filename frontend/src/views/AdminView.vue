<template>
  <div class="page-container admin-page">
    <h1>Administration</h1>

    <div class="admin-sections">
      <!-- Stats -->
      <section class="admin-section">
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
      <section class="admin-section">
        <h2>Import Jobs <button class="btn-sm" @click="refreshImports" style="margin-left:0.5em">↻</button></h2>
        <div v-if="importJobs.length" class="import-list">
          <div v-for="job in importJobs" :key="job.id" class="import-job">
            <div class="job-header" @click="job.expanded = !job.expanded">
              <span class="status-dot" :class="dotClass(job)"></span>
              <span class="job-url">{{ job.url || job.id }}</span>
              <span class="job-elapsed text-muted">{{ elapsed(job) }}</span>
              <span class="status-badge" :class="badgeClass(job)">{{ displayStatus(job) }}</span>
            </div>
            <div v-if="job.expanded" class="job-body">
              <div v-if="job.meta && job.meta.total" class="progress-bar">
                <div class="progress-fill" :style="{ width: (job.meta.current / job.meta.total * 100) + '%' }"></div>
                <span class="progress-label">{{ job.meta.current }} / {{ job.meta.total }}</span>
              </div>
              <div v-if="job.logs.length" class="import-logs">
                <pre class="log-output">{{ job.logs.join('\n') }}</pre>
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
      </section>

      <!-- User Management -->
      <section class="admin-section">
        <h2>User Management</h2>

        <!-- Create user -->
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
                <button v-if="auth.user?.role >= 300 && u.id !== auth.user?.id" class="btn-sm danger" @click="deleteUser(u.id)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="text-muted">No users found.</p>
      </section>

      <!-- Tasks -->
      <section class="admin-section">
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
        </div>
        <p v-if="taskMessage" :class="taskError ? 'text-error' : 'text-success'">{{ taskMessage }}</p>
      </section>

      <!-- Error Log -->
      <section class="admin-section">
        <h2>Recent Errors</h2>
        <table v-if="errors.length">
          <thead><tr><th>Type</th><th>Date</th></tr></thead>
          <tbody>
            <tr v-for="err in errors" :key="err.id">
              <td>{{ err.exception_type }}</td>
              <td>{{ formatDate(err.created_at) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="text-muted">No errors logged.</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const stats = ref(null)
const errors = ref([])
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

const newUser = reactive({ username: '', email: '', password: '', role: 'MEMBER' })
const creatingUser = ref(false)
const createUserMsg = ref('')
const createUserError = ref(false)

const ROLE_VALUES = { 0: 'MEMBER', 1: 'ARTIST', 2: 'PREMIUM', 100: 'HELPER', 200: 'MODERATOR', 300: 'ADMIN', 666: 'OWNER' }
const roles = ['MEMBER', 'ARTIST', 'PREMIUM', 'HELPER', 'MODERATOR', 'ADMIN']

function roleName(val) { return ROLE_VALUES[val] || val }

function jobFailed(job) {
  return job.status === 'FAILURE' || job.status === 'ERROR' || (job.status === 'SUCCESS' && !!job.result?.error)
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
  if (jobFailed(job)) return 'FAILED'
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

onMounted(async () => {
  clockTimer = setInterval(() => { now.value = Date.now() }, 1000)

  // Load import history from localStorage (shared with ImportView)
  try {
    const saved = JSON.parse(localStorage.getItem('importJobs') || '[]')
    for (const s of saved) {
      importJobs.push({
        id: s.id, url: s.url,
        status: s.status || 'PENDING',
        result: s.result || null,
        meta: s.meta || null,
        logs: s.logs || [],
        expanded: false,
        startedAt: s.startedAt || Date.now(),
        finishedAt: s.finishedAt || null,
      })
    }
  } catch { /* ignore */ }

  try {
    const [statsRes, errorsRes] = await Promise.all([
      api.get('/admin/stats'),
      api.get('/admin/errors', { params: { per_page: 10 } }),
    ])
    stats.value = statsRes.data
    errors.value = errorsRes.data.data
  } catch { /* permission guard */ }
  fetchUsers()
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
    const { data } = await api.get('/admin/imports')
    const activeIds = new Set(data.tasks.map(t => t.id))

    // Add new active tasks not yet in the list
    for (const t of data.tasks) {
      let existing = importJobs.find(j => j.id === t.id)
      if (!existing) {
        const job = { id: t.id, url: t.url, status: 'PROGRESS', result: null, meta: null, logs: [], expanded: false, startedAt: Date.now(), finishedAt: null }
        importJobs.unshift(job)
        pollJob(job)
      }
    }

    // Poll any incomplete jobs that disappeared from the active list
    for (const job of importJobs) {
      if (!activeIds.has(job.id) && !['SUCCESS', 'FAILURE', 'ERROR'].includes(job.status)) {
        pollJob(job)
      }
    }

    // Re-sync from localStorage in case ImportView added new entries
    try {
      const saved = JSON.parse(localStorage.getItem('importJobs') || '[]')
      const knownIds = new Set(importJobs.map(j => j.id))
      for (const s of saved) {
        if (!knownIds.has(s.id)) {
          importJobs.push({
            id: s.id, url: s.url,
            status: s.status || 'PENDING',
            result: s.result || null,
            meta: s.meta || null,
            logs: s.logs || [],
            expanded: false,
            startedAt: s.startedAt || Date.now(),
            finishedAt: s.finishedAt || null,
          })
        }
      }
      // Sort by startedAt descending
      importJobs.sort((a, b) => (b.startedAt || 0) - (a.startedAt || 0))
    } catch { /* ignore */ }
  } catch { /* ignore */ }
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
    if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
      job.result = data.result
      job.finishedAt = Date.now()
      if (data.result?.logs) job.logs = data.result.logs
      delete pollTimers[job.id]
    } else {
      pollTimers[job.id] = setTimeout(() => pollJob(job), 2000)
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
</script>

<style scoped>
.admin-sections {
  display: flex;
  flex-direction: column;
  gap: 2em;
  margin-top: 1em;
}
.admin-section h2 {
  margin: 0 0 1em 0;
}

/* Import jobs */
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
.job-elapsed {
  font-size: 0.75rem;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.job-body { padding: 0 0.75rem 0.75rem; }
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
  margin: 0;
}

/* Stats */
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

/* Users */
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
.create-user-form select {
  flex: 1;
  min-width: 10em;
}
.create-user-form button { flex-shrink: 0; }
.role-select {
  background: var(--bg-overlay);
  color: var(--text);
  border: none;
  padding: 2px 4px;
  font-size: 0.85rem;
}

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

/* Tasks */
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

/* Badges */
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

@media (max-width: 689px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
