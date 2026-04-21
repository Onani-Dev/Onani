<template>
  <div class="page-container posts-content">
    <div class="posts-header">
      <h1>Posts</h1>
      <button class="wall-toggle" :title="wallMode ? 'Switch to grid' : 'Switch to wall'" @click="wallMode = !wallMode">
        {{ wallMode ? '\u229e Grid' : '\u25a6 Wall' }}
      </button>
    </div>
    <form class="search-bar" @submit.prevent="search">
      <div class="tag-input-wrap" ref="wrapRef">
        <div class="tag-tokens">
          <span
            v-for="(tok, i) in tokens"
            :key="i"
            class="tag-token"
            :class="tok.startsWith('-') ? 'token-exclude' : 'token-include'"
          >{{ tok }}<button type="button" class="token-remove" @click="removeToken(i)">×</button></span>
        </div>
        <input
          ref="inputRef"
          v-model="inputVal"
          class="tag-input"
          placeholder="Search tags… (space to add, - to exclude)"
          autocomplete="off"
          @input="onInput"
          @keydown="onKeydown"
          @blur="hideSuggestionsDelayed"
        />
        <ul v-if="suggestions.length" class="autocomplete-list">
          <li
            v-for="(tag, i) in suggestions"
            :key="tag.id"
            class="autocomplete-item"
            :class="[`tag-${tag.type}`, { active: i === acIndex }]"
            @mousedown.prevent="pickSuggestion(tag)"
          >
            <span class="ac-name">{{ acPrefix }}{{ tag.name }}</span>
            <span class="ac-count">{{ tag.post_count }}</span>
          </li>
        </ul>
      </div>
      <button type="submit">Search</button>
    </form>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" :per-page="perPage" :total-pages="totalPages" @navigate="goToPage" @update:perPage="onPerPage" />
    <div v-if="posts.length" :class="wallMode ? 'post-wall' : 'post-grid'">
      <PostThumb v-for="post in posts" :key="post.id" :post="post" />
    </div>
    <p v-else-if="!loading" class="no-results">No posts found.</p>
    <Pagination :page="page" :next-page="nextPage" :prev-page="prevPage" :per-page="perPage" :total-pages="totalPages" @navigate="goToPage" @update:perPage="onPerPage" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/client'
import Pagination from '@/components/Pagination.vue'
import PostThumb from '@/components/PostThumb.vue'

const route = useRoute()
const router = useRouter()

const posts = ref([])
const loading = ref(true)
const page = ref(Number(route.query.page) || 1)
const perPage = ref(Number(route.query.per_page) || 30)
const nextPage = ref(null)
const prevPage = ref(null)
const total = ref(0)
const wallMode = ref(false)
const totalPages = computed(() => total.value && perPage.value ? Math.ceil(total.value / perPage.value) : null)

// ── Tag input state ──
// tokens = already-committed tags (e.g. ["dress", "-male"])
// inputVal = currently typed partial token
const tokens = ref((route.query.tags || '').split(' ').filter(Boolean))
const inputVal = ref('')
const suggestions = ref([])
const acIndex = ref(-1)
const inputRef = ref(null)
const wrapRef = ref(null)

// The prefix for the current partial: '-' if the user typed a minus first
const acPrefix = computed(() => inputVal.value.startsWith('-') ? '-' : '')
// The query sent to autocomplete (strip leading '-')
const acQuery = computed(() => inputVal.value.replace(/^-/, ''))

// Full tags string for the API
const tagString = computed(() => tokens.value.join(' '))

let acTimer = null

async function onInput() {
  acIndex.value = -1
  const q = acQuery.value
  if (q.length < 1) { suggestions.value = []; return }
  clearTimeout(acTimer)
  acTimer = setTimeout(async () => {
    try {
      const { data } = await api.get('/tags/autocomplete', { params: { query: q } })
      // Filter out already-added tokens
      suggestions.value = data.data.filter(t => !tokens.value.includes(t.name) && !tokens.value.includes(`-${t.name}`))
    } catch { suggestions.value = [] }
  }, 150)
}

function onKeydown(e) {
  if (suggestions.value.length) {
    if (e.key === 'ArrowDown') { e.preventDefault(); acIndex.value = Math.min(acIndex.value + 1, suggestions.value.length - 1); return }
    if (e.key === 'ArrowUp')   { e.preventDefault(); acIndex.value = Math.max(acIndex.value - 1, -1); return }
    if ((e.key === 'Enter' || e.key === 'Tab') && acIndex.value >= 0) {
      e.preventDefault()
      pickSuggestion(suggestions.value[acIndex.value])
      return
    }
    if (e.key === 'Escape') { suggestions.value = []; acIndex.value = -1; return }
  }
  if (e.key === ' ' || e.key === 'Enter') {
    const val = inputVal.value.trim()
    if (val && val !== '-') {
      if (e.key === ' ') e.preventDefault()
      commitToken(val)
    }
  }
  if (e.key === 'Backspace' && inputVal.value === '' && tokens.value.length) {
    tokens.value.pop()
  }
}

function pickSuggestion(tag) {
  commitToken(`${acPrefix.value}${tag.name}`)
}

function commitToken(val) {
  if (!tokens.value.includes(val)) tokens.value.push(val)
  inputVal.value = ''
  suggestions.value = []
  acIndex.value = -1
}

function removeToken(i) {
  tokens.value.splice(i, 1)
}

function hideSuggestionsDelayed() {
  setTimeout(() => { suggestions.value = [] }, 200)
}

// ── Fetch ──
async function fetchPosts() {
  loading.value = true
  try {
    const params = { page: page.value, per_page: perPage.value }
    if (tagString.value) params.tags = tagString.value
    const { data } = await api.get('/posts', { params })
    posts.value = data.data
    nextPage.value = data.next_page
    prevPage.value = data.prev_page
    total.value = data.total ?? 0
  } finally {
    loading.value = false
  }
}

function search() {
  // commit any partially typed token first
  const partial = inputVal.value.trim()
  if (partial && partial !== '-') commitToken(partial)
  page.value = 1
  const q = { tags: tagString.value || undefined, page: undefined, per_page: perPage.value !== 30 ? perPage.value : undefined }
  router.push({ query: q })
}

function goToPage(p) {
  page.value = p
  router.push({ query: { ...route.query, page: p } })
}

function onPerPage(n) {
  perPage.value = n
  page.value = 1
  router.push({ query: { ...route.query, page: undefined, per_page: n !== 30 ? n : undefined } })
}

watch(() => route.query, () => {
  page.value = Number(route.query.page) || 1
  perPage.value = Number(route.query.per_page) || 30
  tokens.value = (route.query.tags || '').split(' ').filter(Boolean)
  inputVal.value = ''
  fetchPosts()
})

onMounted(fetchPosts)
</script>

<style scoped>
.posts-content {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 50vh;
}
.posts-content h1 { margin: 0.5em; }
.posts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0.5em;
}
.posts-header h1 { margin: 0.3em 0; }
.wall-toggle {
  padding: 0.35em 0.9em;
  font-size: 0.85rem;
  cursor: pointer;
  border: 1px solid var(--border, #444);
  background: var(--bg-raised);
  border-radius: 4px;
  white-space: nowrap;
}
.no-results { padding: 1em; color: var(--text-muted); }

/* Search bar */
.search-bar {
  display: flex;
  gap: 0.5rem;
  margin: 0 0.5em 1em 0.5em;
  align-items: flex-start;
}

/* Tag input wrapper */
.tag-input-wrap {
  flex: 1;
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3em;
  background: var(--bg-input, var(--bg-raised));
  border: 1px solid var(--border, #444);
  border-radius: 4px;
  padding: 0.3em 0.4em;
  cursor: text;
  min-height: 2.2em;
}
.tag-tokens { display: contents; }
.tag-token {
  display: inline-flex;
  align-items: center;
  gap: 0.2em;
  padding: 0.1em 0.45em;
  border-radius: 3px;
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
}
.token-include { background: #1a3a5c; color: #7dd3fc; }
.token-exclude { background: #3a1a1a; color: #fca5a5; }
.token-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.6;
  padding: 0;
  font-size: 0.95em;
  line-height: 1;
}
.token-remove:hover { opacity: 1; }
.tag-input {
  border: none;
  background: transparent;
  outline: none;
  flex: 1;
  min-width: 8em;
  font-size: 0.95rem;
  color: var(--text);
  padding: 0;
}

/* Autocomplete */
.autocomplete-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--bg-overlay, #1e1e1e);
  border: 1px solid var(--border, #444);
  border-radius: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
  z-index: 200;
  max-height: 14em;
  overflow-y: auto;
}
.autocomplete-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.35em 0.7em;
  cursor: pointer;
  font-size: 0.88rem;
  border-left: 3px solid transparent;
}
.autocomplete-item:hover,
.autocomplete-item.active { background: var(--item-hover, #2a2a2a); }
.ac-name { font-weight: 600; }
.ac-count { font-size: 0.78em; color: var(--text-muted); margin-left: 0.5em; }


/* Wall layout */
.post-wall {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 2px;
  width: 100%;
  margin-bottom: 1em;
}
.post-wall :deep(.post-thumb) {
  width: auto;
  height: auto;
  min-width: 80px;
  min-height: 80px;
  padding: 0;
  margin: 0;
  transition: none;
  border-radius: 0;
}
.post-wall :deep(.post-thumb:hover) {
  transform: none;
}
.post-wall :deep(.post-thumb img) {
  max-height: 200px;
  max-width: 300px;
  min-width: unset;
  min-height: unset;
  object-fit: cover;
  border-radius: 0;
  filter: none;
  display: block;
}
</style>

