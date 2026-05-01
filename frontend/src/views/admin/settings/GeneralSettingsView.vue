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
    settings.value = data
  } finally {
    loading.value = false
  }
})

async function save() {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    await updateServerSettings(settings.value)
    success.value = 'Settings saved.'
  } catch (e) {
    error.value = e.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AdminLayout>
    <h2 class="mb-4">General Settings</h2>

    <LoadingSpinner v-if="loading" />

    <form v-else @submit.prevent="save" class="col-lg-6">
      <AlertMessage :message="error" />
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <div class="mb-3">
        <label class="form-label">Server Name</label>
        <input v-model="settings.name" type="text" class="form-control" />
      </div>
      <div class="mb-3">
        <label class="form-label">Max Running Jobs</label>
        <input v-model.number="settings.max_running_jobs" type="number" class="form-control" min="1" />
      </div>
      <div class="mb-3">
        <label class="form-label">Queue Size</label>
        <input v-model.number="settings.queue_size" type="number" class="form-control" min="1" />
      </div>
      <div class="mb-3 form-check">
        <input
          id="maintenance"
          v-model="settings.maintenance"
          type="checkbox"
          class="form-check-input"
        />
        <label for="maintenance" class="form-check-label">Maintenance Mode</label>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="saving">
        <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
        Save
      </button>
    </form>
  </AdminLayout>
</template>
