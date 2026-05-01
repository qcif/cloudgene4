<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getUser, updateUser, deleteUser } from '@/api/users'
import { getToken } from '@/api/auth'
import AlertMessage from '@/components/common/AlertMessage.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const fullName = ref('')
const email = ref('')
const newPassword = ref('')
const confirmNewPassword = ref('')

const error = ref('')
const success = ref('')
const loading = ref(false)
const errors = ref({})

const apiToken = ref(null)
const tokenLoading = ref(false)

const showDeleteConfirm = ref(false)
const deleteLoading = ref(false)

onMounted(async () => {
  const { data } = await getUser(auth.user.id)
  fullName.value = data.full_name || ''
  email.value = data.email || ''
  apiToken.value = data.api_token || null
})

function validate() {
  const e = {}
  if (!fullName.value.trim()) e.fullName = 'Full name is required.'
  if (!email.value.trim()) e.email = 'Email is required.'
  if (newPassword.value) {
    if (newPassword.value.length < 6) e.password = 'Password must be at least 6 characters.'
    else if (!/[A-Z]/.test(newPassword.value)) e.password = 'Password must contain an uppercase letter.'
    else if (!/[0-9]/.test(newPassword.value)) e.password = 'Password must contain a number.'
    if (newPassword.value !== confirmNewPassword.value)
      e.confirmPassword = 'Passwords do not match.'
  }
  errors.value = e
  return Object.keys(e).length === 0
}

async function saveAccount() {
  error.value = ''
  success.value = ''
  if (!validate()) return
  loading.value = true
  try {
    const payload = { full_name: fullName.value, email: email.value }
    if (newPassword.value) payload.password = newPassword.value
    const { data } = await updateUser(auth.user.id, payload)
    auth.updateUser(data)
    success.value = 'Account updated successfully.'
    newPassword.value = ''
    confirmNewPassword.value = ''
  } catch (e) {
    error.value = e.response?.data?.message || 'Update failed.'
  } finally {
    loading.value = false
  }
}

async function createToken() {
  tokenLoading.value = true
  try {
    const { data } = await getToken()
    apiToken.value = data.token
  } finally {
    tokenLoading.value = false
  }
}

async function revokeToken() {
  tokenLoading.value = true
  try {
    await updateUser(auth.user.id, { api_token: null })
    apiToken.value = null
  } finally {
    tokenLoading.value = false
  }
}

async function confirmDelete() {
  deleteLoading.value = true
  try {
    await deleteUser(auth.user.id)
    await auth.logout()
    router.push('/')
  } finally {
    deleteLoading.value = false
    showDeleteConfirm.value = false
  }
}
</script>

<template>
  <div class="container page my-5 p-5">
    <h2>Account Settings</h2>
    <p>Please fill out the form below to change your account settings or your password.</p>
    <br>

    <form id="account-form" class="form-horizontal" @submit.prevent="saveAccount">
      <AlertMessage :message="error" />
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <h4>Personal Information</h4>

      <div class="mb-3">
        <label for="full-name" class="form-label">Full Name:</label>
        <input
          id="full-name"
          v-model="fullName"
          type="text"
          :class="['form-control col-sm-3', errors.fullName ? 'is-invalid' : '']"
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
        />
        <div class="invalid-feedback">{{ errors.email }}</div>
      </div>

      <h4 class="mt-4">Change Password</h4>

      <div class="mb-3">
        <label for="new-password" class="form-label">New Password:</label>
        <input
          id="new-password"
          v-model="newPassword"
          type="password"
          :class="['form-control col-sm-3', errors.password ? 'is-invalid' : '']"
        />
        <div class="invalid-feedback">{{ errors.password }}</div>
      </div>

      <div class="mb-3">
        <label for="confirm-new-password" class="form-label">New Password (again):</label>
        <input
          id="confirm-new-password"
          v-model="confirmNewPassword"
          type="password"
          :class="['form-control col-sm-3', errors.confirmPassword ? 'is-invalid' : '']"
        />
        <div class="invalid-feedback">{{ errors.confirmPassword }}</div>
      </div>

      <div class="mb-3">
        <button class="btn btn-primary" type="submit" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
          Update Account
        </button>
      </div>
    </form>

    <br><hr><br>

    <h3>API Access</h3>
    <p>This service provides a REST API to submit, monitor, and download jobs.</p>
    <p>You need an access token to use the API.</p>

    <div v-if="apiToken">
      <div class="mb-2">
        <code class="user-select-all">{{ apiToken }}</code>
      </div>
      <button class="btn btn-danger" :disabled="tokenLoading" @click="revokeToken">
        <span v-if="tokenLoading" class="spinner-border spinner-border-sm me-1"></span>
        Revoke API Token
      </button>
    </div>
    <div v-else>
      <button class="btn btn-primary" :disabled="tokenLoading" @click="createToken">
        <span v-if="tokenLoading" class="spinner-border spinner-border-sm me-1"></span>
        Create API Token
      </button>
    </div>

    <br><hr><br>

    <h3>Delete Account</h3>
    <p>Once you delete your user account, there is no going back. Please be certain.</p>
    <button class="btn btn-danger" @click="showDeleteConfirm = true">Delete Account</button>

    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="Delete Account"
      message="Are you sure you want to permanently delete your account? This cannot be undone."
      confirm-text="Delete Account"
      :loading="deleteLoading"
      @confirm="confirmDelete"
      @cancel="showDeleteConfirm = false"
    />
  </div>
</template>
