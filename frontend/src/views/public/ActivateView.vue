<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { activate } from '@/api/auth'

const route = useRoute()
const status = ref('loading')
const message = ref('')

onMounted(async () => {
  try {
    const { data } = await activate(route.params.key)
    message.value = data.message || 'Your account has been activated. You can now log in.'
    status.value = 'success'
  } catch (e) {
    message.value = e.response?.data?.message || 'Activation failed. The link may be invalid or expired.'
    status.value = 'error'
  }
})
</script>

<template>
  <div class="container page my-5 p-5">
    <h2>Account Activation</h2>
    <br>
    <div v-if="status === 'loading'" class="text-muted">Activating your account…</div>
    <div v-else-if="status === 'success'" class="alert alert-success">
      {{ message }} <RouterLink to="/login">Login now</RouterLink>.
    </div>
    <div v-else class="alert alert-danger">{{ message }}</div>
  </div>
</template>
