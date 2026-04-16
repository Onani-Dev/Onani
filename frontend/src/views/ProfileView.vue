<template>
  <div class="page-container profile-page">
    <h1>Profile</h1>
    <form @submit.prevent="saveProfile" class="profile-form" v-if="auth.user">
      <div class="field">
        <label>Nickname</label>
        <input v-model="nickname" />
      </div>
      <div class="field">
        <label>Email</label>
        <input v-model="email" type="email" />
      </div>
      <div class="field">
        <label>Site Colour</label>
        <input v-model="profileColour" type="color" @input="applySiteColour" />
      </div>
      <fieldset>
        <legend>Change Password</legend>
        <div class="field">
          <label>Current Password</label>
          <input v-model="currentPassword" type="password" autocomplete="current-password" />
        </div>
        <div class="field">
          <label>New Password</label>
          <input v-model="newPassword" type="password" autocomplete="new-password" />
        </div>
      </fieldset>
      <div class="field">
        <label>
          <input v-model="otpEnabled" type="checkbox" /> Enable 2FA (OTP)
        </label>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="success" class="success">Profile saved.</p>
      <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
    </form>

    <fieldset class="cookies-section" v-if="auth.user">
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
      <p v-if="cookieError" class="error">{{ cookieError }}</p>
      <p v-if="cookieSuccess" class="success">{{ cookieSuccess }}</p>
    </fieldset>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const nickname = ref('')
const email = ref('')
const profileColour = ref('#3391ff')
const currentPassword = ref('')
const newPassword = ref('')
const otpEnabled = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref(false)

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
    applySiteColour()
    otpEnabled.value = auth.user.otp_enabled || false
    loadCookieStatus()
  }
})

async function loadCookieStatus() {
  try {
    const { data } = await api.get('/profile/cookies')
    hasCookies.value = data.has_cookies
  } catch { /* ignore */ }
}

async function saveProfile() {
  saving.value = true
  error.value = ''
  success.value = false

  const payload = {}
  if (nickname.value !== (auth.user.nickname || '')) payload.nickname = nickname.value || null
  if (email.value !== (auth.user.email || '')) {
    payload.email = email.value
    payload.current_password = currentPassword.value
  }
  if (profileColour.value) payload.profile_colour = profileColour.value
  if (newPassword.value) {
    payload.new_password = newPassword.value
    payload.current_password = currentPassword.value
  }
  if (otpEnabled.value !== auth.user.otp_enabled) payload.otp_enabled = otpEnabled.value

  try {
    const { data } = await api.put('/profile', payload)
    auth.user = data
    success.value = true
    currentPassword.value = ''
    newPassword.value = ''
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
.profile-page { max-width: 600px; margin: 0 auto; }
.profile-form { display: flex; flex-direction: column; gap: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.25rem; }
.field label { font-weight: 600; }
fieldset { border: 1px solid #444; padding: 0.75rem; border-radius: 6px; }
.cookies-section { margin-top: 1.5em; }
.cookies-status { color: #8fdf8f; font-size: 0.9rem; margin: 0 0 0.5em; }
.cookies-actions { display: flex; gap: 0.5em; margin-top: 0.5em; }
.btn-danger { background: #5a2d2d; color: #df8f8f; border: none; cursor: pointer; padding: 6px 12px; border-radius: 4px; }
.btn-danger:hover { background: #7a3d3d; }
.text-muted { color: var(--text-muted, #888); font-size: 0.85rem; margin: 0 0 0.75em; }
.error { color: #f66; }
.success { color: #6f6; }
</style>
