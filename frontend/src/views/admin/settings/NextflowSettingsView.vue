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
    settings.value = data.nextflow ?? {}
  } finally {
    loading.value = false
  }
})

async function save() {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    await updateServerSettings({ nextflow: settings.value })
    success.value = 'Nextflow settings saved.'
  } catch (e) {
    error.value = e.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AdminLayout>
    <h2 class="mb-4">Nextflow Settings</h2>

    <LoadingSpinner v-if="loading" />

    <form v-else @submit.prevent="save" class="col-lg-6">
      <AlertMessage :message="error" />
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <div class="mb-3">
        <label class="form-label">Nextflow Binary Path</label>
        <input v-model="settings.binary" type="text" class="form-control" placeholder="/usr/local/bin/nextflow" />
      </div>
      <div class="mb-3">
        <label class="form-label">Work Directory</label>
        <input v-model="settings.work_dir" type="text" class="form-control" placeholder="/tmp/nextflow" />
      </div>
      <div class="mb-3">
        <label class="form-label">Executor</label>
        <select v-model="settings.executor" class="form-select">
          <option value="local">local</option>
          <option value="slurm">slurm</option>
          <option value="sge">sge</option>
          <option value="lsf">lsf</option>
          <option value="awsbatch">awsbatch</option>
        </select>
      </div>
      <div class="row mb-3">
        <div class="col">
          <label class="form-label">Max Memory</label>
          <input v-model="settings.max_memory" type="text" class="form-control" placeholder="8 GB" />
        </div>
        <div class="col">
          <label class="form-label">Max CPUs</label>
          <input v-model.number="settings.max_cpus" type="number" class="form-control" min="1" />
        </div>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="saving">
        <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
        Save
      </button>
    </form>
  </AdminLayout>
</template>
