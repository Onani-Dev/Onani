<template>
  <div class="auth-page">
    <div class="login-box">
      <div class="left-image-container"></div>
      <div class="form-container">
        <h2 class="login-header">Login</h2>
        <form @submit.prevent="handleLogin">
          <input v-model="username" placeholder="Username" required autocomplete="username" />
          <input v-model="password" type="password" placeholder="Password" required autocomplete="current-password" />
          <div v-if="showOtp" class="otp-field">
            <label>OTP Code / Backup Code</label>
            <input v-model="otp" type="text" placeholder="000000 or xxxxxxxx-xxxxxxxx" ref="otpInput" autocomplete="one-time-code" />
            <p class="otp-hint text-muted">Enter your 6-digit authenticator code, or a backup code (e.g. a1b2c3d4-e5f6a7b8).</p>
          </div>
          <p v-if="error && !otpPrompted" class="text-error">{{ error }}</p>
          <button type="submit" :disabled="loading">{{ loading ? 'Logging in...' : 'Login' }}</button>
        </form>
        <div class="login-box-footer">
          <p class="text-muted">Private instance</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const otp = ref('')
const error = ref('')
const loading = ref(false)
const showOtp = ref(false)
const otpPrompted = ref(false)
const otpInput = ref(null)

async function handleLogin() {
  loading.value = true
  error.value = ''
  otpPrompted.value = false
  try {
    await auth.login(username.value, password.value, otp.value || null)
    router.push(route.query.redirect || '/')
  } catch (err) {
    const msg = err.response?.data?.message || 'Login failed.'
    if (msg.toLowerCase().includes('otp') && !showOtp.value) {
      showOtp.value = true
      otpPrompted.value = true
      await nextTick()
      otpInput.value?.focus()
    } else {
      error.value = msg
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
}
.login-box {
  background-color: var(--bg-raised);
  text-align: center;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  margin: 4em auto auto auto;
  min-width: 40em;
  min-height: 30em;
}
.left-image-container {
  background-color: var(--bg-overlay);
  width: 17em;
  min-width: 17em;
  border-bottom-right-radius: 0;
  border-top-right-radius: 0;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
}
.form-container {
  padding: 2em;
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
}
.login-header {
  margin-bottom: 1em;
  user-select: none;
  font-weight: 200;
}
.form-container form {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.form-container input {
  display: flex;
  font-size: medium;
  margin-bottom: 1em;
  padding: 0.7em;
  text-align: left;
  width: 17em;
}
.otp-field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25em;
}
.otp-field label {
  font-size: 0.85rem;
  color: var(--text-muted);
}
.otp-hint {
  font-size: 0.75rem;
  margin: 0;
  text-align: left;
  max-width: 17em;
}
.login-box-footer {
  margin-top: 2em;
  font-size: x-small;
}

@media (max-width: 689px) {
  .login-box {
    min-width: 0;
    min-height: 0;
    margin-top: 2em;
  }
  .left-image-container { display: none; }
  .form-container { padding: 1em; }
  .form-container form { align-items: center; }
  .form-container input { margin: 10px; padding: 15px; }
}
</style>
