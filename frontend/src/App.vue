<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useServerStore } from '@/stores/server'
import AppNavbar from '@/components/layout/AppNavbar.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

const route = useRoute()
const serverStore = useServerStore()

onMounted(() => serverStore.load())
</script>

<template>
  <template v-if="route.path.startsWith('/admin')">
    <RouterView />
  </template>
  <template v-else>
    <AppNavbar />
    <RouterView />
    <AppFooter />
  </template>
</template>
