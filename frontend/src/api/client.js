import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    withCredentials: true,
})

// Fetch a CSRF token once on startup and attach it to every mutating request
let csrfToken = null

async function ensureCsrf() {
    if (!csrfToken) {
        const { data } = await axios.get('/api/v1/auth/csrf', { withCredentials: true })
        csrfToken = data.csrf_token
    }
    return csrfToken
}

api.interceptors.request.use(async (config) => {
    if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
        const token = await ensureCsrf()
        config.headers['X-CSRFToken'] = token
    }
    return config
})

export default api
export { ensureCsrf }
