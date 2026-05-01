import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Public
    { path: '/', component: () => import('@/views/public/HomeView.vue') },
    { path: '/login', component: () => import('@/views/public/LoginView.vue') },
    { path: '/register', component: () => import('@/views/public/RegisterView.vue') },
    { path: '/activate/:key', component: () => import('@/views/public/ActivateView.vue') },
    { path: '/reset-password', component: () => import('@/views/public/PasswordResetView.vue') },
    { path: '/recover/:token', component: () => import('@/views/public/PasswordRecoveryView.vue') },
    { path: '/pages/:slug', component: () => import('@/views/public/StaticPageView.vue') },

    // Auth required
    {
      path: '/profile',
      component: () => import('@/views/public/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/jobs',
      component: () => import('@/views/public/JobListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/jobs/:id',
      component: () => import('@/views/public/JobDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/run/:workflowId',
      component: () => import('@/views/public/WorkflowSubmitView.vue'),
      meta: { requiresAuth: true },
    },

    // Admin required
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminDashboardView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/jobs',
      component: () => import('@/views/admin/AdminJobsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/users',
      component: () => import('@/views/admin/AdminUsersView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/workflows',
      component: () => import('@/views/admin/AdminWorkflowsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/workflows/:id',
      component: () => import('@/views/admin/AdminWorkflowSettingsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/settings/general',
      component: () => import('@/views/admin/settings/GeneralSettingsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/settings/nextflow',
      component: () => import('@/views/admin/settings/NextflowSettingsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/settings/mail',
      component: () => import('@/views/admin/settings/MailSettingsView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/settings/templates',
      component: () => import('@/views/admin/settings/TemplateEditorView.vue'),
      meta: { requiresAdmin: true },
    },
    {
      path: '/admin/settings/logs',
      component: () => import('@/views/admin/settings/LogsView.vue'),
      meta: { requiresAdmin: true },
    },

    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return auth.isLoggedIn ? '/' : '/login'
  }
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { next: to.fullPath } }
  }
})

export default router
