<script setup>
import { ref } from 'vue'
import { requestPasswordReset } from '@/api/auth'
import AlertMessage from '@/components/common/AlertMessage.vue'

const email = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await requestPasswordReset(email.value)
    success.value = 'If an account with that email exists, a reset link has been sent.'
  } catch (e) {
    error.value = e.response?.data?.message || 'Request failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container page my-5 p-5">
    <h2>Reset Password</h2>
    <br>

    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <form v-else @submit.prevent="submit">
      <AlertMessage :message="error" />

      <div class="mb-3">
        <label for="email" class="form-label">E-Mail:</label>
        <input
          id="email"
          v-model="email"
          type="email"
          class="form-control col-sm-3"
          required
        />
      </div>

      <button class="btn btn-primary" type="submit" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
        Send reset link
      </button>
    </form>

    <hr class="mt-4">
    <p><RouterLink to="/login">Back to login</RouterLink></p>
  </div>
</template>
