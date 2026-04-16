<template>
  <div class="auth-page">
    <h1>Register</h1>
    <form @submit.prevent="handleRegister" class="auth-form">
      <div class="field">
        <label>Username</label>
        <input v-model="username" required autocomplete="username" />
      </div>
      <div class="field">
        <label>Email (optional)</label>
        <input v-model="email" type="email" autocomplete="email" />
      </div>
      <div class="field">
        <label>Password</label>
        <input v-model="password" type="password" required autocomplete="new-password" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">{{ loading ? 'Creating...' : 'Register' }}</button>
    </form>
    <p>Already have an account? <router-link to="/login">Login</router-link></p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  loading.value = true
  error.value = ''
  try {
    await auth.register(username.value, password.value, email.value || null)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.message || 'Registration failed.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page { max-width: 400px; margin: 2rem auto; }
.auth-form { display: flex; flex-direction: column; gap: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.25rem; }
.field label { font-weight: 600; }
.error { color: #f66; }
</style>
