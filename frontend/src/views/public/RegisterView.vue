<script setup>
import { ref } from 'vue'
import { register } from '@/api/auth'
import AlertMessage from '@/components/common/AlertMessage.vue'

const username = ref('')
const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')

const error = ref('')
const success = ref('')
const loading = ref(false)
const errors = ref({})

function validate() {
  const e = {}
  if (!username.value.trim()) e.username = 'Username is required.'
  else if (!/^[a-zA-Z0-9_-]{3,}$/.test(username.value))
    e.username = 'Username must be at least 3 characters (letters, numbers, _ -).'
  if (!fullName.value.trim()) e.fullName = 'Full name is required.'
  if (!email.value.trim()) e.email = 'Email address is required.'
  else if (!/\S+@\S+\.\S+/.test(email.value)) e.email = 'Enter a valid email address.'
  if (!password.value) e.password = 'Password is required.'
  else if (password.value.length < 6) e.password = 'Password must be at least 6 characters.'
  else if (!/[A-Z]/.test(password.value)) e.password = 'Password must contain an uppercase letter.'
  else if (!/[0-9]/.test(password.value)) e.password = 'Password must contain a number.'
  if (password.value !== confirmPassword.value)
    e.confirmPassword = 'Passwords do not match.'
  errors.value = e
  return Object.keys(e).length === 0
}

async function submit() {
  error.value = ''
  success.value = ''
  if (!validate()) return

  loading.value = true
  try {
    await register({
      username: username.value,
      full_name: fullName.value,
      email: email.value,
      password: password.value,
    })
    success.value = 'Well done! An email including the activation code has been sent to your address.'
  } catch (e) {
    error.value = e.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container page my-5 p-5">
    <h2>Sign up</h2>
    <br>

    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <form v-else id="signon-form" class="form-horizontal" autocomplete="off" @submit.prevent="submit">
      <AlertMessage :message="error" />

      <div class="mb-3">
        <label for="username" class="form-label">Username:</label>
        <input
          id="username"
          v-model="username"
          type="text"
          :class="['form-control col-sm-3', errors.username ? 'is-invalid' : '']"
          autocomplete="off"
        />
        <div class="invalid-feedback">{{ errors.username }}</div>
      </div>

      <div class="mb-3">
        <label for="full-name" class="form-label">Full Name:</label>
        <input
          id="full-name"
          v-model="fullName"
          type="text"
          :class="['form-control col-sm-3', errors.fullName ? 'is-invalid' : '']"
          autocomplete="off"
        />
        <div class="invalid-feedback">{{ errors.fullName }}</div>
      </div>

      <div class="mb-3">
        <label for="mail" class="form-label">E-Mail:</label>
        <input
          id="mail"
          v-model="email"
          type="text"
          :class="['form-control col-sm-3', errors.email ? 'is-invalid' : '']"
          autocomplete="off"
        />
        <div class="invalid-feedback">{{ errors.email }}</div>
      </div>

      <div class="mb-3">
        <label for="new-password" class="form-label">Password:</label>
        <input
          id="new-password"
          v-model="password"
          type="password"
          :class="['form-control col-sm-3', errors.password ? 'is-invalid' : '']"
          autocomplete="off"
        />
        <div class="invalid-feedback">{{ errors.password }}</div>
      </div>

      <div class="mb-3">
        <label for="confirm-new-password" class="form-label">Confirm password:</label>
        <input
          id="confirm-new-password"
          v-model="confirmPassword"
          type="password"
          :class="['form-control col-sm-3', errors.confirmPassword ? 'is-invalid' : '']"
          autocomplete="off"
        />
        <div class="invalid-feedback">{{ errors.confirmPassword }}</div>
      </div>

      <div class="mb-3">
        <button id="save" class="btn btn-primary" type="submit" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
          Register
        </button>
      </div>
    </form>
  </div>
</template>
