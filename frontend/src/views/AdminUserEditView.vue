<template>
  <div class="page-container admin-user-edit-page">
    <div class="page-header">
      <router-link :to="{ name: 'admin', query: { tab: 'users' } }" class="back-link">← Back to Admin</router-link>
      <h1>Edit User</h1>
    </div>

    <div v-if="loading" class="text-muted">Loading…</div>

    <div v-else-if="user" class="edit-layout">
      <!-- Identity card -->
      <section class="section-card">
        <h2>Identity</h2>
        <p class="user-meta text-muted">
          ID #{{ user.id }} &mdash; joined {{ formatDate(user.created_at) }}
        </p>

        <div class="field">
          <label for="username">Username</label>
          <input id="username" v-model="form.username" />
        </div>
        <div class="field">
          <label for="nickname">Nickname</label>
          <input id="nickname" v-model="form.nickname" placeholder="(none)" />
        </div>
        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="form.email" type="email" placeholder="(none)" />
        </div>
      </section>

      <!-- Password reset -->
      <section class="section-card">
        <h2>Reset Password</h2>
        <div class="field">
          <label for="password">New Password</label>
          <input id="password" v-model="form.password" type="password" placeholder="Leave blank to keep current" autocomplete="new-password" />
        </div>
      </section>

      <!-- Role -->
      <section class="section-card">
        <h2>Role</h2>
        <div class="role-grid">
          <button
            v-for="r in availableRoles"
            :key="r.name"
            type="button"
            class="role-btn"
            :class="{ active: form.role === r.name }"
            @click="form.role = r.name"
          >
            {{ r.name }}
            <span class="role-val">({{ r.value }})</span>
          </button>
        </div>
      </section>

      <!-- Permissions -->
      <section class="section-card">
        <h2>Permissions</h2>

        <div class="permission-presets">
          <span class="presets-label">Presets:</span>
          <button type="button" class="btn-sm" @click="applyPreset('DEFAULT')">DEFAULT</button>
          <button type="button" class="btn-sm" @click="applyPreset('TRUSTED')">TRUSTED</button>
          <button type="button" class="btn-sm" @click="applyPreset('MODERATION')">MODERATION</button>
          <button type="button" class="btn-sm" @click="applyPreset('ADMINISTRATION')">ADMINISTRATION</button>
          <button type="button" class="btn-sm danger" @click="form.permissions = 0">Clear all</button>
        </div>

        <div class="permission-groups">
          <div v-for="group in PERMISSION_GROUPS" :key="group.label" class="perm-group">
            <h3>{{ group.label }}</h3>
            <label v-for="flag in group.flags" :key="flag.name" class="perm-row">
              <input type="checkbox" :checked="hasFlag(flag.value)" @change="toggleFlag(flag.value)" />
              <span class="perm-name">{{ flag.name }}</span>
              <span class="perm-value text-muted">{{ flag.value }}</span>
            </label>
          </div>
        </div>

        <p class="permissions-raw text-muted">Raw value: <code>{{ form.permissions }}</code></p>
      </section>

      <!-- Save -->
      <div class="save-bar">
        <p v-if="successMsg" class="text-success">{{ successMsg }}</p>
        <p v-if="errorMsg" class="text-error">{{ errorMsg }}</p>
        <button class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? 'Saving…' : 'Save Changes' }}
        </button>
      </div>
    </div>

    <p v-else class="text-error">{{ loadError || 'User not found.' }}</p>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const userId = Number(route.params.id)

const user = ref(null)
const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const successMsg = ref('')
const errorMsg = ref('')

const form = reactive({
  username: '',
  nickname: '',
  email: '',
  password: '',
  role: 'MEMBER',
  permissions: 0,
})

// ── Roles ──────────────────────────────────────────────────────────────────
// Only roles that can actually be granted by an admin (not OWNER; the backend
// enforces the hard limit as well)
const availableRoles = [
  { name: 'MEMBER',    value: 0   },
  { name: 'HELPER',    value: 100 },
  { name: 'MODERATOR', value: 200 },
  { name: 'ADMIN',     value: 300 },
  { name: 'OWNER',     value: 666 },
]

// ── Permissions ────────────────────────────────────────────────────────────
const PERMISSION_GROUPS = [
  {
    label: 'Posts',
    flags: [
      { name: 'CREATE_POSTS',   value: 1        },
      { name: 'DELETE_POSTS',   value: 2        },
      { name: 'EDIT_POSTS',     value: 4        },
      { name: 'IMPORT_POSTS',   value: 8        },
      { name: 'MERGE_POSTS',    value: 16       },
    ],
  },
  {
    label: 'Tags',
    flags: [
      { name: 'CREATE_TAGS',    value: 32       },
      { name: 'DELETE_TAGS',    value: 64       },
      { name: 'EDIT_TAGS',      value: 128      },
      { name: 'IMPORT_TAGS',    value: 256      },
      { name: 'MERGE_TAGS',     value: 512      },
    ],
  },
  {
    label: 'Collections',
    flags: [
      { name: 'CREATE_COLLECTIONS', value: 1024  },
      { name: 'DELETE_COLLECTIONS', value: 2048  },
      { name: 'EDIT_COLLECTIONS',   value: 4096  },
      { name: 'MERGE_COLLECTIONS',  value: 8192  },
    ],
  },
  {
    label: 'Flagging',
    flags: [
      { name: 'CAN_FLAG',       value: 16384    },
      { name: 'PRIORITY_FLAG',  value: 32768    },
    ],
  },
  {
    label: 'Comments',
    flags: [
      { name: 'CREATE_COMMENTS', value: 65536   },
      { name: 'DELETE_COMMENTS', value: 131072  },
      { name: 'LOCK_COMMENTS',   value: 262144  },
    ],
  },
  {
    label: 'News',
    flags: [
      { name: 'CREATE_NEWS',    value: 524288   },
      { name: 'DELETE_NEWS',    value: 1048576  },
      { name: 'EDIT_NEWS',      value: 2097152  },
    ],
  },
  {
    label: 'Users',
    flags: [
      { name: 'BAN_USERS',      value: 4194304  },
      { name: 'CREATE_USERS',   value: 8388608  },
      { name: 'DELETE_USERS',   value: 16777216 },
      { name: 'EDIT_USERS',     value: 33554432 },
    ],
  },
  {
    label: 'Site',
    flags: [
      { name: 'BYPASS_RATELIMIT', value: 67108864  },
      { name: 'VIEW_LOGS',        value: 134217728 },
    ],
  },
]

// Permission presets (must match backend IntFlag values)
const PRESETS = {
  DEFAULT:        1 | 65536 | 1024 | 16384,
  TRUSTED:        (1 | 65536 | 1024 | 16384) | 32 | 8 | 32768,
  MODERATION:     (1 | 65536 | 1024 | 16384) | 32 | 8 | 32768 | 4 | 16 | 128 | 512 | 4096 | 8192 | 131072 | 262144,
  ADMINISTRATION: (1 | 65536 | 1024 | 16384) | 32 | 8 | 32768 | 4 | 16 | 128 | 512 | 4096 | 8192 | 131072 | 262144
                  | 2 | 64 | 2048 | 524288 | 1048576 | 2097152 | 4194304 | 8388608 | 16777216 | 33554432 | 67108864 | 134217728,
}

function hasFlag(value) {
  return (form.permissions & value) === value
}

function toggleFlag(value) {
  if (hasFlag(value)) {
    form.permissions &= ~value
  } else {
    form.permissions |= value
  }
}

function applyPreset(name) {
  form.permissions = PRESETS[name]
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const { data } = await api.get('/admin/user', { params: { user_id: userId } })
    user.value = data
    form.username    = data.username ?? ''
    form.nickname    = data.nickname ?? ''
    form.email       = data.email    ?? ''
    form.password    = ''
    form.role        = roleIntToName(data.role_int)
    form.permissions = data.permissions_int ?? 0
  } catch (err) {
    console.error('AdminUserEdit fetch failed:', err)
    const status = err.response?.status
    if (status === 401) {
      router.push({ name: 'login', query: { redirect: route.fullPath } })
      return
    }
    loadError.value = err.response?.data?.description || err.response?.data?.message ||
      (status ? `Error ${status}` : 'Network error — check your connection.')
  } finally {
    loading.value = false
  }
})

const ROLE_VALUE_MAP = { 0: 'MEMBER', 100: 'HELPER', 200: 'MODERATOR', 300: 'ADMIN', 666: 'OWNER' }
function roleIntToName(val) { return ROLE_VALUE_MAP[val] || 'MEMBER' }

// ── Save ───────────────────────────────────────────────────────────────────
async function save() {
  successMsg.value = ''
  errorMsg.value = ''
  saving.value = true

  const payload = {
    user_id:     userId,
    username:    form.username  || undefined,
    nickname:    form.nickname  || null,
    email:       form.email     || null,
    role:        form.role,
    permissions: form.permissions,
  }
  if (form.password) payload.password = form.password

  try {
    const { data } = await api.put('/admin/user', payload)
    user.value = data
    form.password = ''
    successMsg.value = 'User updated successfully.'
  } catch (err) {
    errorMsg.value = err.response?.data?.message || err.response?.data?.description || 'An error occurred.'
  } finally {
    saving.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.admin-user-edit-page {
  max-width: 860px;
}

.page-header {
  margin-bottom: 1.5rem;
}

.back-link {
  display: inline-block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  opacity: 0.7;
}

.user-meta {
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.edit-layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-card {
  background: var(--surface, #1e1e2e);
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
}

.section-card h2 {
  margin: 0 0 1rem;
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.6;
}

.field {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field label {
  font-size: 0.875rem;
  font-weight: 500;
}

.field input {
  padding: 0.45rem 0.65rem;
  border-radius: 5px;
  border: 1px solid var(--border, #333);
  background: var(--input-bg, #181825);
  color: inherit;
  font-size: 0.95rem;
  width: 100%;
  box-sizing: border-box;
}

/* Role grid */
.role-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.role-btn {
  padding: 0.4rem 0.85rem;
  border-radius: 5px;
  border: 1px solid var(--border, #333);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.15s, border-color 0.15s;
}

.role-btn:hover {
  background: var(--hover, #2a2a3c);
}

.role-btn.active {
  background: var(--accent, #89b4fa);
  color: #000;
  border-color: var(--accent, #89b4fa);
}

.role-val {
  font-size: 0.75rem;
  opacity: 0.65;
}

/* Permissions */
.permission-presets {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 1.25rem;
}

.presets-label {
  font-size: 0.8rem;
  opacity: 0.6;
  margin-right: 0.25rem;
}

.btn-sm {
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  border: 1px solid var(--border, #333);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 0.8rem;
}

.btn-sm:hover { background: var(--hover, #2a2a3c); }
.btn-sm.danger { border-color: #f38ba8; color: #f38ba8; }
.btn-sm.danger:hover { background: rgba(243,139,168,0.12); }

.permission-groups {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}

.perm-group h3 {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.5;
  margin: 0 0 0.4rem;
}

.perm-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.2rem 0;
  cursor: pointer;
  font-size: 0.875rem;
}

.perm-name { flex: 1; }
.perm-value { font-size: 0.72rem; }

.permissions-raw {
  margin-top: 1rem;
  font-size: 0.8rem;
}

/* Save bar */
.save-bar {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.btn-primary {
  padding: 0.55rem 1.4rem;
  border-radius: 6px;
  border: none;
  background: var(--accent, #89b4fa);
  color: #000;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.95rem;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.text-success { color: #a6e3a1; }
.text-error   { color: #f38ba8; }
.text-muted   { opacity: 0.55; }
</style>
