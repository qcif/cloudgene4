<script setup>
import AdminSidebar from './AdminSidebar.vue'
</script>

<template>
  <div class="d-flex" style="min-height: 100vh;">
    <AdminSidebar />
    <main class="flex-grow-1 p-4 bg-white">
      <slot />
    </main>
  </div>
</template>
