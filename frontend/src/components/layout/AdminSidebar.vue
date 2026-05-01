<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <nav class="admin-sidebar d-flex flex-column p-3" style="min-width: 220px;">
    <RouterLink class="navbar-brand mb-3 ps-2 text-dark fw-bold" to="/">
      <i class="fas fa-dna me-2"></i>Cloudgene
    </RouterLink>

    <ul class="nav flex-column">
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin">
          <i class="fas fa-tachometer-alt"></i> Dashboard
        </RouterLink>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/jobs">
          <i class="fas fa-tasks"></i> Jobs
        </RouterLink>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/users">
          <i class="fas fa-users"></i> Users
        </RouterLink>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/workflows">
          <i class="fas fa-sitemap"></i> Workflows
        </RouterLink>
      </li>

      <li class="nav-item mt-3 mb-1">
        <small class="text-muted text-uppercase ps-2 fw-semibold" style="font-size:0.7rem;">Settings</small>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/settings/general">
          <i class="fas fa-cog"></i> General
        </RouterLink>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/settings/nextflow">
          <i class="fas fa-stream"></i> Nextflow
        </RouterLink>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/settings/mail">
          <i class="fas fa-envelope"></i> Mail
        </RouterLink>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/settings/templates">
          <i class="fas fa-file-code"></i> Templates
        </RouterLink>
      </li>
      <li class="nav-item mb-1">
        <RouterLink class="nav-link" to="/admin/settings/logs">
          <i class="fas fa-scroll"></i> Logs
        </RouterLink>
      </li>

      <li class="nav-item mt-auto pt-4">
        <RouterLink class="nav-link" to="/">
          <i class="fas fa-arrow-left"></i> Back to Site
        </RouterLink>
      </li>
      <li class="nav-item">
        <button class="nav-link btn btn-link text-start w-100" @click="logout">
          <i class="fas fa-sign-out-alt"></i> Logout
        </button>
      </li>
    </ul>
  </nav>
</template>
