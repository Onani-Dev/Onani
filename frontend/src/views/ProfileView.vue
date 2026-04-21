<template>
  <div class="profile-page page-container">
    <div class="profile-layout">
      <nav class="profile-tabs" aria-label="Profile sections">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="tab-item"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </nav>

      <div class="profile-content">
        <div class="profile-header">
          <button type="button" class="avatar-wrapper" title="Edit avatar" @click="avatarControlsOpen = !avatarControlsOpen">
            <img v-if="avatarPreview || auth.user?.settings?.avatar" :src="avatarPreview || auth.user.settings.avatar" class="avatar" />
            <div v-else class="avatar avatar-placeholder">{{ initial }}</div>
            <div class="avatar-overlay">Edit</div>
          </button>
          <input type="file" ref="avatarInput" accept="image/*" class="avatar-file-input" @change="onAvatarChange" />
          <div class="header-info">
            <h1>{{ auth.user?.nickname || auth.user?.username }}</h1>
            <p class="text-muted">{{ auth.user?.username }}</p>
            <p class="text-muted" v-if="auth.user?.created_at">Joined {{ formatDateShort(auth.user.created_at) }}</p>
            <div v-if="avatarControlsOpen" class="avatar-action-row">
              <button type="button" class="btn-secondary btn-sm" @click="triggerAvatarUpload">Upload Avatar</button>
              <button type="button" class="btn-secondary btn-sm" @click="revertAvatar" :disabled="!avatarPreview">Discard</button>
              <button type="button" class="btn-danger btn-sm" @click="removeAvatar" :disabled="saving || (!auth.user?.settings?.avatar && !avatarPreview)">Remove</button>
              <button type="button" class="btn-secondary btn-sm" @click="avatarControlsOpen = false">Done</button>
              <span v-if="avatarPreview" class="avatar-pending text-muted">New avatar selected, save to apply.</span>
            </div>
          </div>
        </div>

        <form @submit.prevent="saveProfile" class="profile-sections">
          <!-- General -->
          <section v-show="activeTab === 'general'" class="section-card">
            <h2>General</h2>
            <div class="field">
              <label for="nickname">Nickname</label>
              <input id="nickname" v-model="nickname" placeholder="Display name" />
            </div>
            <div class="field">
              <label for="email">Email</label>
              <input id="email" v-model="email" type="email" placeholder="you@example.com" />
            </div>
            <div class="btn-row">
              <button type="button" class="btn-secondary btn-sm" @click="revertGeneral">Revert</button>
            </div>
          </section>

          <!-- Appearance -->
          <section v-show="activeTab === 'appearance'" class="section-card">
            <h2>Appearance</h2>
            <div class="field colour-field">
              <label for="colour">Site Colour</label>
              <div class="colour-row">
                <input id="colour" v-model="profileColour" type="color" class="colour-picker" @input="applySiteColour" />
                <span class="colour-hex">{{ profileColour }}</span>
              </div>
              <div class="btn-row">
                <button type="button" class="btn-secondary btn-sm" @click="resetSiteColour">Reset to default</button>
              </div>
            </div>
          </section>

          <!-- Content -->
          <section v-show="activeTab === 'content'" class="section-card">
            <h2>Content</h2>
            <div class="field field-toggle">
              <label for="sfwmode">SFW Mode</label>
              <input id="sfwmode" v-model="sfwMode" type="checkbox" class="toggle-checkbox" />
              <p class="field-hint">Blur explicit and questionable images until you click to reveal them.</p>
            </div>
          </section>

          <!-- Security -->
          <section v-show="activeTab === 'security'" class="section-card">
            <h2>Security</h2>
            <div class="field">
              <label for="curpw">Current Password</label>
              <input id="curpw" v-model="currentPassword" type="password" autocomplete="current-password" />
            </div>
            <div class="field-row">
              <div class="field">
                <label for="newpw">New Password</label>
                <input id="newpw" v-model="newPassword" type="password" autocomplete="new-password" />
              </div>
              <div class="field">
                <label for="confirmpw">Confirm New Password</label>
                <input id="confirmpw" v-model="confirmPassword" type="password" autocomplete="new-password" :class="{ 'input-mismatch': confirmPassword && confirmPassword !== newPassword }" />
              </div>
            </div>
            <p v-if="confirmPassword && confirmPassword !== newPassword" class="text-error" style="font-size:0.8rem;margin-top:-0.5rem">Passwords do not match.</p>

            <div class="otp-section">
              <div class="otp-status-row">
                <span class="dot" :class="otpEnabled ? 'dot-active' : 'dot-inactive'"></span>
                <span>Two-Factor Authentication</span>
                <span class="otp-badge" :class="otpEnabled ? 'badge-on' : 'badge-off'">
                  {{ otpEnabled ? 'Enabled' : 'Disabled' }}
                </span>
              </div>

              <template v-if="!otpEnabled">
                <template v-if="!otpSetupVisible">
                  <button type="button" class="btn-secondary btn-sm" @click="startOtpSetup" :disabled="otpLoading">
                    {{ otpLoading ? 'Loading...' : 'Set up 2FA' }}
                  </button>
                </template>
                <template v-else>
                  <div class="otp-setup-box">
                    <p class="text-muted">Scan this code with your authenticator app, then enter the 6-digit code to confirm.</p>
                    <img v-if="otpQrCode" :src="otpQrCode" class="qr-code" alt="OTP QR code" />
                    <button type="button" class="btn-link" @click="showSecret = !showSecret">
                      {{ showSecret ? 'Hide secret key' : "Can't scan? Show secret key" }}
                    </button>
                    <div v-if="showSecret" class="otp-secret-box">
                      <code class="otp-secret">{{ otpSecret }}</code>
                    </div>
                    <div class="field otp-verify-field">
                      <label for="otpcode">Verification Code</label>
                      <input id="otpcode" v-model="otpCode" type="number" placeholder="000000" maxlength="6" />
                      <div class="otp-verify-row">
                        <button type="button" @click="verifyOtp" :disabled="otpLoading">
                          {{ otpLoading ? 'Verifying...' : 'Verify & Enable' }}
                        </button>
                        <button type="button" class="btn-secondary" @click="otpSetupVisible = false">Cancel</button>
                      </div>
                    </div>
                    <p v-if="otpError" class="text-error">{{ otpError }}</p>
                  </div>
                </template>
              </template>

              <template v-else>
                <div class="field otp-verify-field">
                  <label for="disable-otp-password">Current Password (required to disable)</label>
                  <input id="disable-otp-password" v-model="otpDisablePassword" type="password" autocomplete="current-password" />
                  <button type="button" class="btn-danger btn-sm" @click="disableOtp" :disabled="otpLoading || !otpDisablePassword">
                    {{ otpLoading ? 'Disabling...' : 'Disable 2FA' }}
                  </button>
                </div>
              </template>
            </div>
          </section>

          <!-- Import Cookies -->
          <section v-show="activeTab === 'cookies'" class="section-card">
            <h2>Import Cookies</h2>
            <p class="text-muted">Upload a Netscape-format cookies.txt for gallery-dl. Stored encrypted with your password.</p>
            <div class="cookie-status-row" v-if="hasCookies">
              <span class="dot dot-active"></span>
              <span>Cookies file stored</span>
            </div>
            <div class="field">
              <label for="cookiepw">Password (required to encrypt)</label>
              <input id="cookiepw" v-model="cookiePassword" type="password" autocomplete="current-password" />
            </div>
            <div class="field">
              <input type="file" ref="cookieFileInput" accept=".txt,.cookies" />
            </div>
            <div class="btn-row">
              <button type="button" class="btn-secondary" @click="uploadCookies" :disabled="cookieUploading">{{ cookieUploading ? 'Uploading...' : 'Upload Cookies' }}</button>
              <button type="button" v-if="hasCookies" @click="deleteCookies" class="btn-danger">Remove Cookies</button>
            </div>
            <p v-if="cookieError" class="text-error">{{ cookieError }}</p>
            <p v-if="cookieSuccess" class="text-success">{{ cookieSuccess }}</p>
          </section>

          <div class="save-bar">
            <p v-if="error" class="text-error">{{ error }}</p>
            <p v-if="success" class="text-success">Profile saved.</p>
            <span v-if="hasUnsavedChanges" class="text-muted">Unsaved changes</span>
            <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const activeTab = ref('general')
const tabs = [
  { id: 'general', label: 'General', icon: '👤' },
  { id: 'appearance', label: 'Appearance', icon: '🎨' },
  { id: 'content', label: 'Content', icon: '🖼️' },
  { id: 'security', label: 'Security', icon: '🔐' },
  { id: 'cookies', label: 'Cookies', icon: '🍪' },
]

const initial = computed(() => {
  const name = auth.user?.nickname || auth.user?.username || '?'
  return name.charAt(0).toUpperCase()
})

const nickname = ref('')
const email = ref('')
const profileColour = ref('#3391ff')
const sfwMode = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const saving = ref(false)
const error = ref('')
const success = ref(false)
const removeProfilePicture = ref(false)

// Avatar
const avatarPreview = ref(null)
const avatarInput = ref(null)
const avatarBase64 = ref(null)
const avatarControlsOpen = ref(false)

// OTP — fetched from server on mount, not relying on stale auth.user
const otpEnabled = ref(false)
const otpSetupVisible = ref(false)
const otpQrCode = ref(null)
const otpSecret = ref(null)
const showSecret = ref(false)
const otpCode = ref('')
const otpLoading = ref(false)
const otpError = ref('')
const otpDisablePassword = ref('')

// Cookies
const hasCookies = ref(false)
const cookiePassword = ref('')
const cookieUploading = ref(false)
const cookieError = ref('')
const cookieSuccess = ref('')
const cookieFileInput = ref(null)

const originalProfile = ref({
  nickname: '',
  email: '',
  profile_colour: '#3391ff',
  sfw_mode: false,
})

const hasUnsavedChanges = computed(() => {
  return (
    nickname.value !== originalProfile.value.nickname ||
    email.value !== originalProfile.value.email ||
    profileColour.value !== originalProfile.value.profile_colour ||
    sfwMode.value !== originalProfile.value.sfw_mode ||
    !!avatarBase64.value ||
    removeProfilePicture.value ||
    !!newPassword.value
  )
})

onMounted(() => {
  bootstrapProfile()
})

async function bootstrapProfile() {
  try {
    const { data } = await api.get('/profile')
    auth.user = data
    nickname.value = data.nickname || ''
    email.value = data.email || ''
    profileColour.value = data.settings?.profile_colour || '#3391ff'
    sfwMode.value = data.settings?.sfw_mode ?? false
    originalProfile.value = {
      nickname: nickname.value,
      email: email.value,
      profile_colour: profileColour.value,
      sfw_mode: sfwMode.value,
    }
  } catch {
    if (auth.user) {
      nickname.value = auth.user.nickname || ''
      email.value = auth.user.email || ''
      profileColour.value = auth.user.settings?.profile_colour || '#3391ff'
      sfwMode.value = auth.user.settings?.sfw_mode ?? false
    }
  } finally {
    applySiteColour()
    loadCookieStatus()
    loadOtpStatus()
  }
}

async function loadOtpStatus() {
  try {
    const { data } = await api.get('/profile/otp')
    otpEnabled.value = data.enabled
  } catch { /* ignore */ }
}

async function loadCookieStatus() {
  try {
    const { data } = await api.get('/profile/cookies')
    hasCookies.value = data.has_cookies
  } catch { /* ignore */ }
}

function onAvatarChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    avatarBase64.value = ev.target.result
    avatarPreview.value = ev.target.result
    removeProfilePicture.value = false
    avatarControlsOpen.value = true
  }
  reader.readAsDataURL(file)
}

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

function revertAvatar() {
  avatarBase64.value = null
  avatarPreview.value = null
  removeProfilePicture.value = false
  if (avatarInput.value) avatarInput.value.value = ''
}

function revertGeneral() {
  nickname.value = originalProfile.value.nickname
  email.value = originalProfile.value.email
}

async function saveProfile() {
  if (newPassword.value && newPassword.value !== confirmPassword.value) {
    error.value = 'New passwords do not match.'
    return
  }
  saving.value = true
  error.value = ''
  success.value = false

  const payload = {}
  // Send '' to clear nickname — backend converts '' to null via `value or None`
  if (nickname.value !== (auth.user.nickname || '')) payload.nickname = nickname.value
  if (email.value !== (auth.user.email || '')) {
    payload.email = email.value
    payload.current_password = currentPassword.value
  }
  if (profileColour.value) payload.profile_colour = profileColour.value
  payload.sfw_mode = sfwMode.value
  if (newPassword.value) {
    payload.new_password = newPassword.value
    payload.current_password = currentPassword.value
  }
  if (avatarBase64.value) payload.profile_picture = avatarBase64.value
  if (removeProfilePicture.value) payload.remove_profile_picture = true

  try {
    const { data } = await api.put('/profile', payload)
    auth.user = data
    success.value = true
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    revertAvatar()
    originalProfile.value = {
      nickname: data.nickname || '',
      email: data.email || '',
      profile_colour: data.settings?.profile_colour || '#3391ff',
      sfw_mode: data.settings?.sfw_mode ?? false,
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}

function resetSiteColour() {
  profileColour.value = '#3391ff'
  applySiteColour()
}

async function removeAvatar() {
  error.value = ''
  success.value = false
  saving.value = true
  try {
    const { data } = await api.put('/profile', { remove_profile_picture: true })
    auth.user = data
    revertAvatar()
    removeProfilePicture.value = false
    success.value = true
  } catch (err) {
    error.value = err.response?.data?.message || 'Avatar remove failed.'
  } finally {
    saving.value = false
  }
}

function applySiteColour() {
  const hex = profileColour.value
  const s = document.documentElement.style
  s.setProperty('--accent', hex)
  s.setProperty('--link', hex)
  s.setProperty('--accent-hover', `color-mix(in srgb, ${hex} 80%, black)`)
  s.setProperty('--link-hover', `color-mix(in srgb, ${hex} 70%, white)`)
}

async function startOtpSetup() {
  otpLoading.value = true
  otpError.value = ''
  try {
    const { data } = await api.get('/profile/otp')
    otpQrCode.value = data.qr_code
    otpSecret.value = data.secret
    showSecret.value = false
    otpSetupVisible.value = true
  } catch { otpError.value = 'Failed to load OTP setup.' }
  finally { otpLoading.value = false }
}

async function verifyOtp() {
  if (!otpCode.value) return
  otpLoading.value = true
  otpError.value = ''
  try {
    await api.post('/profile/otp', { code: Number(otpCode.value) })
    otpEnabled.value = true
    otpSetupVisible.value = false
    otpQrCode.value = null
    otpSecret.value = null
    showSecret.value = false
    otpCode.value = ''
  } catch (err) {
    otpError.value = err.response?.data?.message || 'Invalid code.'
  } finally { otpLoading.value = false }
}

async function disableOtp() {
  otpLoading.value = true
  otpError.value = ''
  try {
    await api.delete('/profile/otp', { data: { password: otpDisablePassword.value } })
    otpEnabled.value = false
    otpDisablePassword.value = ''
  } catch (err) {
    otpError.value = err.response?.data?.message || 'Disable 2FA failed.'
  }
  finally { otpLoading.value = false }
}

function formatDateShort(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString()
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
    const { data } = await api.post('/profile/cookies', form, {
      headers: { 'Content-Type': undefined },
    })
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
.profile-page {
  width: min(50vw, 58rem);
  margin: 0 auto;
  padding: 0;
  overflow: hidden;
}

.profile-layout {
  display: flex;
  gap: 0;
  min-height: 60vh;
}

.profile-tabs {
  display: flex;
  flex-direction: column;
  width: 11em;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  background: var(--bg-overlay);
}

.profile-content {
  flex: 1;
  min-width: 0;
  padding: 1.5rem;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 0.45em;
  border: none;
  background: none;
  color: var(--text);
  text-align: left;
  font: inherit;
  font-size: 0.88rem;
  padding: 0.65em 0.9em;
  cursor: pointer;
  border-left: 3px solid transparent;
}

.tab-item:hover {
  background: var(--item-hover);
}

.tab-item.active {
  background: var(--item-hover);
  border-left-color: var(--accent, #5a8a5a);
  font-weight: 600;
}

.tab-icon { flex-shrink: 0; }

/* ── Header ──────────────────────────────────────────── */
.profile-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
  cursor: pointer;
  width: 72px;
  height: 72px;
  border: none;
  background: none;
  padding: 0;
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-raised);
  border: 2px solid var(--border);
  color: var(--text-muted);
  font-size: 1.8rem;
  font-weight: 700;
  user-select: none;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
}
.avatar-wrapper:hover .avatar-overlay { opacity: 1; }

.avatar-file-input {
  display: none;
}

.header-info h1 { margin: 0; line-height: 1.2; }
.header-info .text-muted { font-size: 0.9rem; margin: 0; }

.avatar-action-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 0.6rem;
  flex-wrap: wrap;
}

.avatar-pending {
  font-size: 0.78rem;
}

/* ── Section cards ───────────────────────────────────── */
.profile-sections {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-card {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  padding: 1.25rem;
}

.section-card h2 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text);
}

/* ── Fields ──────────────────────────────────────────── */
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-bottom: 0.75rem;
}
.field:last-child { margin-bottom: 0; }

.field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

/* ── Colour picker ───────────────────────────────────── */
.colour-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.colour-picker {
  width: 40px;
  height: 40px;
  padding: 2px;
  cursor: pointer;
  border: 1px solid var(--border);
}

.colour-hex {
  font-size: 0.85rem;
  font-family: 'Consolas', 'Fira Code', monospace;
  color: var(--text-muted);
}

.input-mismatch {
  outline: 1px solid var(--error) !important;
}

/* ── OTP ─────────────────────────────────────────────── */
.otp-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
  margin-top: 0.75rem;
}

.otp-status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.otp-badge {
  margin-left: auto;
  padding: 0.1em 0.55em;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}
.badge-on { background: #1d3d1d; color: #8fdf8f; }
.badge-off { background: #3a2d2d; color: #dfafaf; }

.qr-code {
  width: 180px;
  height: 180px;
  border-radius: 6px;
  image-rendering: pixelated;
  display: block;
  margin: 0 auto;
}

.otp-setup-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  text-align: center;
}

.btn-link {
  background: none;
  border: none;
  padding: 0;
  color: var(--accent, #7aa2f7);
  font-size: 0.85rem;
  cursor: pointer;
  text-decoration: underline;
}
.btn-link:hover { opacity: 0.8; }

.otp-secret-box {
  background: var(--surface2, #1e1e2e);
  border: 1px solid var(--border, #414168);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  word-break: break-all;
}

.otp-secret {
  font-family: monospace;
  font-size: 1rem;
  letter-spacing: 0.1em;
  user-select: all;
}

.otp-verify-field {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.otp-verify-field input {
  width: 100%;
  font-size: 1.1rem;
  letter-spacing: 0.15em;
  text-align: center;
}

.otp-verify-row {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

/* ── Cookie status ───────────────────────────────────── */
.cookie-status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

/* ── Dots ────────────────────────────────────────────── */
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-active { background: #8fdf8f; }
.dot-inactive { background: #888; }

/* ── Button row ──────────────────────────────────────── */
.btn-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-sm {
  padding: 0.3rem 0.75rem;
  font-size: 0.85rem;
}

.btn-secondary {
  background: var(--bg-overlay);
  color: var(--text);
  border: 1px solid var(--border);
}
.btn-secondary:hover { background: var(--item-hover); }

.btn-danger {
  background: #5a2d2d;
  color: #df8f8f;
}
.btn-danger:hover { background: #7a3d3d; }

/* ── Save bar ────────────────────────────────────────── */
.save-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: flex-end;
}

.save-bar .text-error,
.save-bar .text-success {
  margin: 0;
  font-size: 0.9rem;
}

/* ── Utilities ───────────────────────────────────────── */
.text-muted { color: var(--text-muted); font-size: 0.85rem; }
.text-error { color: var(--error); }
.text-success { color: var(--success); }

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 500px) {
  .profile-page { padding: 0; }
  .profile-layout { flex-direction: column; }
  .profile-tabs {
    flex-direction: row;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
  }
  .tab-item {
    border-left: none;
    border-bottom: 3px solid transparent;
    flex-direction: column;
    gap: 0.15em;
    font-size: 0.75rem;
    padding: 0.55em 0.75em;
  }
  .tab-item.active {
    border-bottom-color: var(--accent, #5a8a5a);
    border-left-color: transparent;
  }
  .profile-sections { padding-left: 0; padding-top: 0.75rem; }
  .profile-content { padding: 0.75rem 0 0 0; }
  .field-row { grid-template-columns: 1fr; }
  .profile-header { gap: 1rem; }
  .avatar-action-row { margin-top: 0.45rem; }
  .avatar, .avatar-wrapper { width: 56px; height: 56px; }
  .otp-verify-row { flex-wrap: wrap; }
}

@media (max-width: 1200px) {
  .profile-page {
    width: min(92vw, 58rem);
  }
}

/* ── Toggle field (SFW mode etc.) ────────────────────── */
.field-toggle {
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.field-toggle label {
  flex: 1;
  margin-bottom: 0;
  font-size: 0.9rem;
  text-transform: none;
  letter-spacing: normal;
  color: var(--text);
}
.toggle-checkbox {
  width: 1.1rem;
  height: 1.1rem;
  accent-color: var(--accent);
  cursor: pointer;
  flex-shrink: 0;
}
.field-hint {
  width: 100%;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0;
}
</style>
