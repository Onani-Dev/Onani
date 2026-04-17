<template>
  <div class="home">

    <!-- Top row: Random post + Explore tags side by side -->
    <div class="home-top-row">

      <!-- Random post -->
      <div v-if="data.random" class="index-post-group home-top-random">
        <div class="post-group-header">
          <h2>Random Post</h2>
          <router-link :to="`/posts/${data.random.id}`">#{{ data.random.id }} →</router-link>
        </div>
        <div class="spotlight-tile">
          <router-link :to="`/posts/${data.random.id}`" class="spotlight-link">
            <img :src="data.random.thumbnail_url" class="spotlight-img" :alt="`Post #${data.random.id}`" :class="{ 'sfw-blurred': shouldBlur(data.random) }" />
          </router-link>
          <div v-if="shouldBlur(data.random)" class="sfw-overlay spotlight-sfw-overlay" @click.stop="reveal(data.random.id)">Click to reveal</div>
        </div>
      </div>

      <!-- Explore tags -->
      <div v-if="data.tags?.length" class="index-post-group home-top-tags">
        <div class="post-group-header">
          <h2>Explore Tags</h2>
          <router-link to="/tags">Browse All →</router-link>
        </div>
        <div class="tag-cloud">
          <router-link
            v-for="tag in data.tags"
            :key="tag.id"
            :to="`/tags/${tag.id}`"
            class="tag-pill"
            :class="`tag-${tag.type}`"
          >{{ tag.name }} <span class="tag-count">{{ tag.post_count }}</span></router-link>
        </div>
      </div>

    </div>

    <!-- Hot posts -->
    <div class="index-post-group">
      <div class="post-group-header">
        <h2>🔥 Hot Posts</h2>
        <router-link to="/posts">View All →</router-link>
      </div>
      <div class="post-group-grid">
        <router-link v-for="post in data.hot" :key="post.id" :to="`/posts/${post.id}`" class="post-thumb">
          <img :src="post.thumbnail_url" :alt="`Post #${post.id}`" loading="lazy" :class="{ 'sfw-blurred': shouldBlur(post) }" />
          <div v-if="shouldBlur(post)" class="sfw-overlay" @click.stop="reveal(post.id)">Show</div>
        </router-link>
        <p v-if="!loading && !data.hot?.length" class="empty-msg">No hot posts yet.</p>
      </div>
    </div>

    <!-- Recent posts -->
    <div class="index-post-group">
      <div class="post-group-header">
        <h2>Recent Posts</h2>
        <router-link to="/posts">View All →</router-link>
      </div>
      <div class="post-group-grid">
        <router-link v-for="post in data.recent" :key="post.id" :to="`/posts/${post.id}`" class="post-thumb">
          <img :src="post.thumbnail_url" :alt="`Post #${post.id}`" loading="lazy" :class="{ 'sfw-blurred': shouldBlur(post) }" />
          <div v-if="shouldBlur(post)" class="sfw-overlay" @click.stop="reveal(post.id)">Show</div>
        </router-link>
        <p v-if="!loading && !data.recent.length" class="empty-msg">No posts yet.</p>
      </div>
    </div>

    <!-- Popular posts -->
    <div class="index-post-group">
      <div class="post-group-header">
        <h2>Popular Posts</h2>
        <router-link to="/posts">View All →</router-link>
      </div>
      <div class="post-group-grid">
        <router-link v-for="post in data.popular" :key="post.id" :to="`/posts/${post.id}`" class="post-thumb">
          <img :src="post.thumbnail_url" :alt="`Post #${post.id}`" loading="lazy" :class="{ 'sfw-blurred': shouldBlur(post) }" />
          <div v-if="shouldBlur(post)" class="sfw-overlay" @click.stop="reveal(post.id)">Show</div>
        </router-link>
        <p v-if="!loading && !data.popular.length" class="empty-msg">No posts yet.</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'
import { useSfwMode } from '@/composables/useSfwMode'

const { shouldBlur, reveal } = useSfwMode()

const data = ref({ recent: [], hot: [], popular: [], random: null, tags: [] })
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
/* Top row: random post + tags side by side */
.home-top-row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1em;
  margin-bottom: 1em;
  align-items: start;
}
.home-top-random {
  width: fit-content;
  min-width: 12em;
  max-width: 32em;
  margin-bottom: 0;
}
.home-top-tags {
  min-width: 0;
  margin-bottom: 0;
}

/* Spotlight tile */
.spotlight-tile {
  background-color: var(--bg-overlay);
  padding: 0.75em;
  border-radius: 0 0 15px 15px;
  display: flex;
  justify-content: center;
  height: calc(100% - 2.6em); /* fill below header */
  position: relative;
  overflow: hidden;
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

/* Shared group */
.index-post-group { margin-bottom: 1em; }
.post-group-header {
  padding: 10px;
  background-color: var(--header-bg);
  border-radius: 15px 15px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.post-group-header a { color: var(--text-muted); }
.empty-msg { padding: 1em; color: var(--text-muted); }
.post-group-grid {
  background-color: var(--bg-overlay);
  padding: 10px 10px 1.5em 10px;
  min-height: 10em;
  border-radius: 0 0 15px 15px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(11em, 1fr));
}

/* Tag cloud */
.tag-cloud {
  background-color: var(--bg-overlay);
  padding: 1em;
  border-radius: 0 0 15px 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em;
  align-content: flex-start;
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
  .home-top-random { width: 100%; max-width: 100%; }
  .post-group-grid { grid-template-columns: repeat(auto-fill, minmax(6em, 1fr)); }
}
@media (min-width: 690px) and (max-width: 1110px) {
  .post-group-grid { grid-template-columns: repeat(auto-fill, minmax(9em, 1fr)); }
}
</style>
