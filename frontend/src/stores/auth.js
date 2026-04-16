import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null)
    const loading = ref(true)

    const isAuthenticated = computed(() => !!user.value)

    async function fetchUser() {
        try {
            const { data } = await api.get('/auth/me')
            if (data.authenticated) {
                user.value = data
            } else {
                user.value = null
            }
        } catch {
            user.value = null
        } finally {
            loading.value = false
        }
    }

    async function login(username, password, otp = null) {
        const payload = { username, password }
        if (otp) payload.otp = otp
        const { data } = await api.post('/auth/login', payload)
        user.value = data
        return data
    }

    async function logout() {
        await api.post('/auth/logout')
        user.value = null
    }

    return { user, loading, isAuthenticated, fetchUser, login, logout }
})
