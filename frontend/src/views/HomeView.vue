<template>
  <div class="home page-container">
    <section class="home-top-row">
      <article v-if="data.random" class="home-panel random-panel">
        <header class="panel-header">
          <h2>Random Spotlight</h2>
          <router-link :to="`/posts/${data.random.id}`">#{{ data.random.id }} →</router-link>
        </header>
        <div class="spotlight-tile">
          <router-link :to="`/posts/${data.random.id}`" class="spotlight-link">
            <img :src="data.random.thumbnail_url" class="spotlight-img" :alt="`Post #${data.random.id}`" :class="{ 'sfw-blurred': shouldBlur(data.random) }" />
          </router-link>
          <div v-if="shouldBlur(data.random)" class="sfw-overlay spotlight-sfw-overlay" @click.stop="reveal(data.random.id)">Click to reveal</div>
        </div>
      </article>

      <article v-if="data.tags?.length" class="home-panel tags-panel">
        <header class="panel-header">
          <h2>Explore Tags</h2>
          <router-link to="/tags">Browse All →</router-link>
        </header>
        <div class="tag-cloud">
          <router-link
            v-for="tag in data.tags"
            :key="tag.id"
            :to="`/tags/${tag.id}`"
            class="tag-pill"
            :class="`tag-${tag.type}`"
          >{{ tag.name }} <span class="tag-count">{{ tag.post_count }}</span></router-link>
        </div>
      </article>
    </section>

    <section class="home-panel">
      <header class="panel-header">
        <h2>Recent Posts</h2>
        <router-link to="/posts">View All →</router-link>
      </header>
      <div class="post-group-grid">
        <PostThumb v-for="post in data.recent" :key="post.id" :post="post" />
        <p v-if="!loading && !data.recent.length" class="empty-msg">No posts yet.</p>
      </div>
    </section>

    <section class="home-panel">
      <header class="panel-header">
        <h2>Popular Posts</h2>
        <router-link to="/posts">View All →</router-link>
      </header>
      <div class="post-group-grid">
        <PostThumb v-for="post in data.popular" :key="post.id" :post="post" />
        <p v-if="!loading && !data.popular.length" class="empty-msg">No posts yet.</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import { useSfwMode } from '@/composables/useSfwMode'
import PostThumb from '@/components/PostThumb.vue'

const { shouldBlur, reveal } = useSfwMode()

const data = ref({ recent: [], popular: [], random: null, tags: [] })
const loading = ref(true)

onMounted(async () => {
  try {
    const { data: d } = await api.get('/posts/home')
    data.value = d
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.home {
  display: grid;
  gap: 1em;
}

.home-top-row {
  display: grid;
  grid-template-columns: minmax(16em, 1fr) 1.35fr;
  gap: 1em;
  align-items: start;
}

.home-panel {
  background: var(--bg-overlay);
  border: 1px solid var(--border);
  padding: 0.8em;
  border-radius: 0;
}

.spotlight-tile {
  margin-top: 0.65em;
  background-color: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  padding: 0.65em;
  display: flex;
  justify-content: center;
  min-height: 13em;
  position: relative;
  overflow: hidden;
  border-radius: 0;
}
.spotlight-link { display: block; line-height: 0; }
.spotlight-img {
  width: auto;
  max-width: 100%;
  max-height: 22em;
  object-fit: contain;
  border-radius: 8px;
  display: block;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.6em;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5em;
  border-radius: 0;
}

.panel-header h2 {
  font-size: 1.05rem;
}

.panel-header a { color: var(--text-muted); }

.empty-msg { padding: 1em; color: var(--text-muted); }
.post-group-grid {
  padding: 0.8em 0.15em 0.3em;
  min-height: 10em;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(10.5em, 1fr));
  border-radius: 0;
}

.tag-cloud {
  padding: 0.8em 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em;
  align-content: flex-start;
  border-radius: 0;
}
.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  padding: 0.25em 0.65em;
  border-radius: 999px;
  font-size: 0.85rem;
  background: var(--bg-raised);
  color: var(--text);
  text-decoration: none;
  border: 1px solid transparent;
  transition: background 0.15s;
}
.tag-pill:hover { background: var(--item-hover); }
.tag-count { font-size: 0.75em; color: var(--text-muted); }

@media (max-width: 689px) {
  .home-top-row { grid-template-columns: 1fr; }
  .post-group-grid { grid-template-columns: repeat(auto-fill, minmax(6em, 1fr)); }
}
@media (min-width: 690px) and (max-width: 1110px) {
  .post-group-grid { grid-template-columns: repeat(auto-fill, minmax(9em, 1fr)); }
}
</style>
