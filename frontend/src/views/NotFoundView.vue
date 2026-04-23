<template>
  <div class="page-container error-page">
    <img src="/static/image/404.gif" alt="404" class="error-image" />
    <h1>404</h1>
    <p>The page you're looking for doesn't exist.</p>
    <router-link to="/">Go home</router-link>
  </div>
</template>

<style scoped>
.error-page { text-align: center; margin-top: 4rem; }
.error-image { display: block; margin: 0 auto 1.5rem; max-width: 300px; }
.error-page h1 { font-size: 4rem; margin-bottom: 0.5rem; }
</style>
