<template>
  <div class="app-layout">
    <header class="navbar">
      <router-link to="/" class="brand"><img id="logo" :src="'/static/svg/onani.svg'" alt="Onani" /></router-link>
      <div class="site-links">
        <router-link to="/posts">Posts</router-link>
        <router-link to="/tags">Tags</router-link>
        <router-link to="/collections">Collections</router-link>
        <router-link to="/import">Import</router-link>
        <router-link to="/upload">Upload</router-link>
      </div>
      <div class="nav-right">
        <template v-if="auth.isAuthenticated">
          <div class="user-menu">
            <span class="user-menu-trigger">{{ auth.user?.username }}</span>
            <div class="user-dropdown">
              <router-link to="/profile">Profile</router-link>
              <router-link v-if="auth.user?.role >= 200" to="/admin">Administration</router-link>
              <a href="#" @click.prevent="handleLogout">Logout</a>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="login-register-buttons">
            <router-link to="/login">Login</router-link>
          </div>
        </template>
      </div>
    </header>
    <main class="main-content">
      <router-view />
    </main>
    <footer>
      <a href="#">Onani</a>
    </footer>
  </div>
</template>

<script setup>
import { watchEffect } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function applyColour(hex) {
  const s = document.documentElement.style
  s.setProperty('--accent', hex)
  s.setProperty('--link', hex)
  s.setProperty('--accent-hover', `color-mix(in srgb, ${hex} 80%, black)`)
  s.setProperty('--link-hover', `color-mix(in srgb, ${hex} 70%, white)`)
}

watchEffect(() => {
  const colour = auth.user?.settings?.profile_colour
  if (colour) applyColour(colour)
})

async function handleLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  height: var(--header-height);
  max-height: var(--header-height);
  justify-content: left;
  margin-bottom: 0;
  text-align: left;
}

.brand {
  cursor: pointer;
  display: inline-flex;
  align-self: center;
  margin-left: 10px;
  margin-right: 10px;
  text-decoration: none;
}
#logo {
  display: inline-block;
  width: 6em;
  margin-top: auto;
  margin-bottom: auto;
}

.site-links {
  display: flex;
  height: var(--header-height);
  max-height: var(--header-height);
  align-items: center;
}
.site-links a {
  align-self: center;
  color: var(--text-muted);
  display: inline-flex;
  font-size: 16px;
  padding: 14px 16px;
  text-align: center;
  text-decoration: none;
  vertical-align: middle;
  transition: background-color 0.15s;
  border-radius: 0;
}
.site-links a:hover {
  background-color: var(--item-hover);
  color: var(--text);
}
.site-links a.router-link-active {
  color: var(--text);
}

.nav-right {
  display: flex;
  margin-left: auto;
  align-items: center;
}

.login-register-buttons {
  align-self: center;
  cursor: pointer;
  display: inline-flex;
  margin-right: 15px;
}
.login-register-buttons a {
  align-self: center;
  color: var(--text-muted);
  display: inline-flex;
  font-size: 16px;
  padding: 14px 16px;
  text-align: center;
  text-decoration: none;
  border-radius: 0;
}
.login-register-buttons a:hover {
  background-color: var(--item-hover);
  color: var(--text);
}

.user-menu {
  position: relative;
  align-self: center;
  margin-right: 15px;
}
.user-menu-trigger {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 16px;
  padding: 14px 16px;
  user-select: none;
  border-radius: 0;
}
.user-menu-trigger:hover {
  color: var(--text);
}
.user-dropdown {
  display: none;
  position: absolute;
  right: 0;
  top: 100%;
  background-color: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: 0.4em;
  min-width: 10em;
  z-index: 100;
  flex-direction: column;
  overflow: hidden;
}
.user-menu:hover .user-dropdown {
  display: flex;
}
.user-dropdown a {
  color: var(--text-muted);
  text-decoration: none;
  padding: 0.7em 1em;
  border-radius: 0;
  transition: background-color 0.15s;
  white-space: nowrap;
}
.user-dropdown a:hover {
  background-color: var(--item-hover);
  color: var(--text);
}

.main-content {
  flex: 1;
  padding: 20px;
}

footer {
  align-content: center;
  align-items: center;
  background-color: var(--bg-overlay);
  border-radius: 15px 15px 0 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 50px;
  min-height: 60px;
  width: 100%;
}
footer a {
  margin: 1em;
  color: var(--text-muted);
  text-decoration: none;
}

@media (max-width: 689px) {
  .site-links { display: none; }
  .login-register-buttons { display: none; }
  .user-profile-card { display: none; }
  .brand { margin-left: 20px; margin-right: 20px; }
}
@media (min-width: 690px) and (max-width: 1110px) {
  .site-links { display: none; }
  .login-register-buttons { display: none; }
  .user-profile-card { display: none; }
  .brand { margin-left: 20px; margin-right: 20px; }
}
</style>
