<template>
  <div v-if="article" class="page-container">
    <h1>{{ article.title }}</h1>
    <p class="meta">{{ article.type }} · {{ article.created_at }}</p>
    <div v-html="article.content"></div>
  </div>
  <p v-else>Loading...</p>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/client'

const props = defineProps({ id: [String, Number] })
const article = ref(null)

onMounted(async () => {
  const { data } = await api.get('/news', { params: { id: props.id } })
  article.value = data
})
</script>
