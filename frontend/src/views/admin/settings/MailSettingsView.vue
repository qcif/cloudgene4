<script setup>
import { ref, onMounted } from 'vue'
import { getServerSettings, updateServerSettings } from '@/api/admin'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import AlertMessage from '@/components/common/AlertMessage.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const settings = ref({})
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')

onMounted(async () => {
  try {
    const { data } = await getServerSettings()
    settings.value = data.mail ?? {}
  } finally {
    loading.value = false
  }
})

async function save() {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    await updateServerSettings({ mail: settings.value })
    success.value = 'Mail settings saved.'
  } catch (e) {
    error.value = e.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AdminLayout>
    <h2 class="mb-4">Mail Settings</h2>

    <LoadingSpinner v-if="loading" />

    <form v-else @submit.prevent="save" class="col-lg-6">
      <AlertMessage :message="error" />
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <div class="mb-3">
        <label class="form-label">SMTP Host</label>
        <input v-model="settings.host" type="text" class="form-control" placeholder="smtp.example.com" />
      </div>
      <div class="mb-3">
        <label class="form-label">SMTP Port</label>
        <input v-model.number="settings.port" type="number" class="form-control" placeholder="587" />
      </div>
      <div class="mb-3">
        <label class="form-label">Username</label>
        <input v-model="settings.username" type="text" class="form-control" />
      </div>
      <div class="mb-3">
        <label class="form-label">Password</label>
        <input v-model="settings.password" type="password" class="form-control" />
      </div>
      <div class="mb-3">
        <label class="form-label">From Address</label>
        <input v-model="settings.from_address" type="email" class="form-control" />
      </div>
      <div class="mb-3 form-check">
        <input id="tls" v-model="settings.use_tls" type="checkbox" class="form-check-input" />
        <label for="tls" class="form-check-label">Use TLS</label>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="saving">
        <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
        Save
      </button>
    </form>
  </AdminLayout>
</template>
