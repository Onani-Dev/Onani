<template>
  <router-link :to="`/posts/${resolvedId}`" :target="target || undefined" class="post-thumb">
    <div v-if="!imageLoaded && post.thumbnail_url" class="thumb-loader" />
    <img
      v-if="post.thumbnail_url"
      :src="post.thumbnail_url"
      :alt="`Post #${resolvedId}`"
      loading="lazy"
      :class="{ 'sfw-blurred': shouldBlur(post, resolvedId) }"
      @load="imageLoaded = true"
    />
    <span v-else class="thumb-missing">#{{ resolvedId }}</span>
    <div v-if="shouldBlur(post, resolvedId)" class="sfw-overlay" @click.stop="reveal(resolvedId)">Show</div>
  </router-link>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSfwMode } from '@/composables/useSfwMode'

const props = defineProps({
  post: { type: Object, required: true },
  postId: { type: [String, Number], default: null },
  target: { type: String, default: null },
})

const { shouldBlur, reveal } = useSfwMode()
const resolvedId = computed(() => props.postId ?? props.post.id)
const imageLoaded = ref(false)
</script>

<style>
.thumb-missing {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: var(--bg-raised);
  color: var(--text-muted);
  font-size: 0.8rem;
}
</style>
