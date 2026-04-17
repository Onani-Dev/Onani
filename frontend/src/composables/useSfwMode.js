import { reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const NSFW_RATINGS = new Set(['q', 'e'])

export function useSfwMode() {
    const auth = useAuthStore()
    const revealed = reactive(new Set())

    const sfwMode = computed(() => auth.user?.settings?.sfw_mode === true)

    function isNsfw(post) {
        return NSFW_RATINGS.has((post.rating || '').toLowerCase())
    }

    function shouldBlur(post, id) {
        const key = id ?? post.id
        return sfwMode.value && isNsfw(post) && !revealed.has(key)
    }

    function reveal(id) {
        revealed.add(id)
    }

    return { sfwMode, shouldBlur, reveal }
}
