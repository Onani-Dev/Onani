<template>
  <div class="profile-page">
    <!-- Recovery codes modal -->
    <div v-if="showRecoveryModal" class="modal-overlay" @click.self="showRecoveryModal = false">
      <div class="modal-box">
        <h3>🔑 Save Your Recovery Codes</h3>
        <p class="text-muted">Store these codes in a safe place. Each code can only be used <strong>once</strong> to log in if you lose access to your authenticator app.</p>
        <div class="recovery-codes-grid">
          <code v-for="code in recoveryCodes" :key="code" class="recovery-code">{{ code }}</code>
        </div>
        <div class="btn-row" style="justify-content: flex-end; margin-top: 1rem;">
          <button type="button" @click="copyRecoveryCodes">📋 Copy All</button>
          <button type="button" @click="showRecoveryModal = false">I've saved my codes</button>
        </div>
      </div>
    </div>

    <!-- User header -->
    <div class="profile-header">
      <label class="avatar-wrapper" title="Change avatar">
        <img v-if="avatarPreview || auth.user?.settings?.avatar" :src="avatarPreview || auth.user.settings.avatar" class="avatar" />
        <div v-else class="avatar avatar-placeholder">{{ initial }}</div>
        <div class="avatar-overlay">Change</div>
        <input type="file" ref="avatarInput" accept="image/*" class="avatar-file-input" @change="onAvatarChange" />
      </label>
      <div class="header-info">
        <h1>{{ auth.user?.nickname || auth.user?.username }}</h1>
        <p class="text-muted">{{ auth.user?.username }}</p>
      </div>
    </div>

    <form @submit.prevent="saveProfile" class="profile-sections">
      <!-- General -->
      <section class="section-card">
        <h2>General</h2>
        <div class="field">
          <label for="nickname">Nickname</label>
          <input id="nickname" v-model="nickname" placeholder="Display name" />
        </div>
        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" placeholder="you@example.com" />
        </div>
      </section>

      <!-- Appearance -->
      <section class="section-card">
        <h2>Appearance</h2>
        <div class="field colour-field">
          <label for="colour">Site Colour</label>
          <div class="colour-row">
            <input id="colour" v-model="profileColour" type="color" class="colour-picker" @input="applySiteColour" />
            <span class="colour-hex">{{ profileColour }}</span>
          </div>
        </div>
      </section>

      <!-- Content -->
      <section class="section-card">
        <h2>Content</h2>
        <div class="field field-toggle">
          <label for="sfwmode">SFW Mode</label>
          <input id="sfwmode" v-model="sfwMode" type="checkbox" class="toggle-checkbox" />
          <p class="field-hint">Blur explicit and questionable images until you click to reveal them.</p>
        </div>
      </section>

      <!-- Security -->
      <section class="section-card">
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

          <!-- Setup flow (shown when not enabled) -->
          <template v-if="!otpEnabled">
            <template v-if="!otpSetupVisible">
              <button type="button" class="btn-secondary btn-sm" @click="startOtpSetup" :disabled="otpLoading">
                {{ otpLoading ? 'Loading...' : 'Set up 2FA' }}
              </button>
            </template>
            <template v-else>
              <p class="text-muted">Scan this code with your authenticator app, then enter the 6-digit code to confirm.</p>
              <img v-if="otpQrCode" :src="otpQrCode" class="qr-code" alt="OTP QR code" />
              <details class="otp-secret-details">
                <summary class="text-muted">Can't scan the QR code?</summary>
                <div class="field" style="margin-top: 0.5rem;">
                  <label>Secret Key (enter manually)</label>
                  <code class="otp-secret">{{ otpSecret }}</code>
                </div>
              </details>
              <div class="field otp-verify-field">
                <label for="otpcode">Verification Code</label>
                <div class="otp-verify-row">
                  <input id="otpcode" v-model="otpCode" type="number" placeholder="000000" maxlength="6" />
                  <button type="button" @click="verifyOtp" :disabled="otpLoading">
                    {{ otpLoading ? 'Verifying...' : 'Verify & Enable' }}
                  </button>
                  <button type="button" class="btn-secondary" @click="otpSetupVisible = false">Cancel</button>
                </div>
              </div>
              <p v-if="otpError" class="text-error">{{ otpError }}</p>
            </template>
          </template>

          <!-- Disable / regenerate flow (shown when enabled) -->
          <template v-else>
            <div class="btn-row">
              <button type="button" class="btn-danger btn-sm" @click="disableOtp" :disabled="otpLoading">
                {{ otpLoading ? 'Disabling...' : 'Disable 2FA' }}
              </button>
              <button type="button" class="btn-secondary btn-sm" @click="regenOtpToken" :disabled="otpLoading">
                {{ otpLoading ? 'Regenerating...' : 'Regenerate Token' }}
              </button>
            </div>
          </template>
        </div>
      </section>

      <!-- Import Cookies -->
      <section class="section-card">
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

      <!-- Save -->
      <div class="save-bar">
        <p v-if="error" class="text-error">{{ error }}</p>
        <p v-if="success" class="text-success">Profile saved.</p>
        <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

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

// Avatar
const avatarPreview = ref(null)
const avatarInput = ref(null)
const avatarBase64 = ref(null)

// OTP — fetched from server on mount, not relying on stale auth.user
const otpEnabled = ref(false)
const otpSetupVisible = ref(false)
const otpQrCode = ref(null)
const otpSecret = ref('')
const otpCode = ref('')
const otpLoading = ref(false)
const otpError = ref('')
const showRecoveryModal = ref(false)
const recoveryCodes = ref([])

// Cookies
const hasCookies = ref(false)
const cookiePassword = ref('')
const cookieUploading = ref(false)
const cookieError = ref('')
const cookieSuccess = ref('')
const cookieFileInput = ref(null)

onMounted(() => {
  if (auth.user) {
    nickname.value = auth.user.nickname || ''
    email.value = auth.user.email || ''
    profileColour.value = auth.user.settings?.profile_colour || '#3391ff'
    sfwMode.value = auth.user.settings?.sfw_mode ?? false
    applySiteColour()
    loadCookieStatus()
    loadOtpStatus()
  }
})

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
  }
  reader.readAsDataURL(file)
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

  try {
    const { data } = await api.put('/profile', payload)
    auth.user = data
    success.value = true
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    avatarBase64.value = null
  } catch (err) {
    error.value = err.response?.data?.message || 'Save failed.'
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
    otpSetupVisible.value = true
  } catch { otpError.value = 'Failed to load OTP setup.' }
  finally { otpLoading.value = false }
}

async function verifyOtp() {
  if (!otpCode.value) return
  otpLoading.value = true
  otpError.value = ''
  try {
    const { data } = await api.post('/profile/otp', { code: Number(otpCode.value) })
    otpEnabled.value = true
    otpSetupVisible.value = false
    otpQrCode.value = null
    otpSecret.value = ''
    otpCode.value = ''
    if (data.backup_codes?.length) {
      recoveryCodes.value = data.backup_codes
      showRecoveryModal.value = true
    }
  } catch (err) {
    otpError.value = err.response?.data?.message || 'Invalid code.'
  } finally { otpLoading.value = false }
}

async function disableOtp() {
  otpLoading.value = true
  try {
    await api.delete('/profile/otp')
    otpEnabled.value = false
  } catch { /* ignore */ }
  finally { otpLoading.value = false }
}

async function regenOtpToken() {
  otpLoading.value = true
  otpError.value = ''
  try {
    const { data } = await api.put('/profile/otp')
    otpEnabled.value = false
    otpQrCode.value = data.qr_code
    otpSecret.value = data.secret
    otpSetupVisible.value = true
  } catch { otpError.value = 'Failed to regenerate OTP token.' }
  finally { otpLoading.value = false }
}

function copyRecoveryCodes() {
  navigator.clipboard?.writeText(recoveryCodes.value.join('\n'))
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
  max-width: 640px;
  margin: 0 auto;
}

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

/* ── Section cards ───────────────────────────────────── */
.profile-sections {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
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
}

.otp-verify-field {
  max-width: 360px;
}

.otp-verify-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.otp-verify-row input {
  width: 8em;
  font-size: 1.1rem;
  letter-spacing: 0.15em;
  text-align: center;
}

.otp-secret-details {
  font-size: 0.85rem;
  color: var(--text-muted);
}
.otp-secret-details summary {
  cursor: pointer;
  user-select: none;
}
.otp-secret {
  display: inline-block;
  margin-top: 0.25rem;
  padding: 0.3rem 0.6rem;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  border-radius: 4px;
  font-family: 'Consolas', 'Fira Code', monospace;
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  word-break: break-all;
  user-select: all;
}

/* ── Recovery codes modal ────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  max-width: 480px;
  width: 90%;
}

.modal-box h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
}

.recovery-codes-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
  margin: 1rem 0;
}

.recovery-code {
  display: block;
  padding: 0.3rem 0.5rem;
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  border-radius: 4px;
  font-family: 'Consolas', 'Fira Code', monospace;
  font-size: 0.85rem;
  text-align: center;
  letter-spacing: 0.05em;
  user-select: all;
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
  .field-row { grid-template-columns: 1fr; }
  .profile-header { gap: 1rem; }
  .avatar, .avatar-wrapper { width: 56px; height: 56px; }
  .otp-verify-row { flex-wrap: wrap; }
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
