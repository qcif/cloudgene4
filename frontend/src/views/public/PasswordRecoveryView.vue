<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { confirmPasswordReset } from '@/api/auth'
import AlertMessage from '@/components/common/AlertMessage.vue'

const route = useRoute()
const router = useRouter()

const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  try {
    await confirmPasswordReset(route.params.token, password.value)
    router.push('/login')
  } catch (e) {
    error.value = e.response?.data?.message || 'Password reset failed. The link may be expired.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container page my-5 p-5">
    <h2>Set New Password</h2>
    <br>

    <form @submit.prevent="submit">
      <AlertMessage :message="error" />

      <div class="mb-3">
        <label for="new-password" class="form-label">New Password:</label>
        <input
          id="new-password"
          v-model="password"
          type="password"
          class="form-control col-sm-3"
          required
        />
      </div>

      <div class="mb-3">
        <label for="confirm-password" class="form-label">Confirm Password:</label>
        <input
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          class="form-control col-sm-3"
          required
        />
      </div>

      <button class="btn btn-primary" type="submit" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
        Set password
      </button>
    </form>
  </div>
</template>
