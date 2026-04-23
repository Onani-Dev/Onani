import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import DefaultLayout from '@/layouts/DefaultLayout.vue'

const routes = [
    {
        path: '/',
        component: DefaultLayout,
        meta: { requiresAuth: true },
        children: [
            { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
            { path: 'posts', name: 'posts', component: () => import('@/views/PostsView.vue') },
            { path: 'posts/:id', name: 'post', component: () => import('@/views/PostView.vue'), props: true },
            { path: 'tags', name: 'tags', component: () => import('@/views/TagsView.vue') },
            { path: 'tags/:id', name: 'tag', component: () => import('@/views/TagView.vue'), props: true },
            { path: 'users', name: 'users', component: () => import('@/views/UsersView.vue') },
            { path: 'users/:id', name: 'user', component: () => import('@/views/UserView.vue'), props: true },
            { path: 'news', name: 'news', component: () => import('@/views/NewsView.vue') },
            { path: 'news/:id', name: 'article', component: () => import('@/views/ArticleView.vue'), props: true },
            { path: 'collections', name: 'collections', component: () => import('@/views/CollectionsView.vue') },
            { path: 'collections/:id', name: 'collection', component: () => import('@/views/CollectionView.vue'), props: true },
            { path: 'import', name: 'import', component: () => import('@/views/ImportView.vue') },
            { path: 'upload', name: 'upload', component: () => import('@/views/UploadView.vue') },
            { path: 'profile', name: 'profile', component: () => import('@/views/ProfileView.vue') },
            { path: 'favourites', name: 'favourites', component: () => import('@/views/FavouritesView.vue') },
            { path: 'admin', name: 'admin', component: () => import('@/views/AdminView.vue') },
            { path: 'admin/users/:id/edit', name: 'adminUserEdit', component: () => import('@/views/AdminUserEditView.vue'), props: true },
        ],
    },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/403', name: 'forbidden', component: () => import('@/views/ForbiddenView.vue') },
    { path: '/429', name: 'rateLimit', component: () => import('@/views/RateLimitView.vue') },
    { path: '/418', name: 'teapot', component: () => import('@/views/TeapotView.vue') },
    { path: '/:pathMatch(.*)*', name: 'notFound', component: () => import('@/views/NotFoundView.vue') },
]

const router = createRouter({
    history: createWebHistory('/'),
    routes,
})

router.beforeEach(async (to) => {
    const auth = useAuthStore()
    if (auth.loading) {
        await auth.fetchUser()
    }
    const needsAuth = to.matched.some(record => record.meta.requiresAuth)
    if (needsAuth && !auth.isAuthenticated) {
        return { name: 'login', query: { redirect: to.fullPath } }
    }
})

export default router
