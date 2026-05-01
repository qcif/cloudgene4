<script setup>
import { ref, onMounted } from 'vue'
import { getTemplates, updateTemplate } from '@/api/admin'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import AlertMessage from '@/components/common/AlertMessage.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const templates = ref([])
const loading = ref(true)
const saving = ref(null)
const error = ref('')
const success = ref('')

onMounted(async () => {
  try {
    const { data } = await getTemplates()
    templates.value = data
  } finally {
    loading.value = false
  }
})

async function save(tmpl) {
  error.value = ''
  success.value = ''
  saving.value = tmpl.id
  try {
    await updateTemplate(tmpl.id, { content: tmpl.content })
    success.value = `Template "${tmpl.name}" saved.`
  } catch (e) {
    error.value = e.response?.data?.message || 'Save failed.'
  } finally {
    saving.value = null
  }
}
</script>

<template>
  <AdminLayout>
    <h2 class="mb-4">Page Templates</h2>

    <AlertMessage :message="error" />
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <LoadingSpinner v-if="loading" />

    <div v-else>
      <div v-for="tmpl in templates" :key="tmpl.id" class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
          <strong>{{ tmpl.name }}</strong>
          <button
            class="btn btn-sm btn-primary"
            :disabled="saving === tmpl.id"
            @click="save(tmpl)"
          >
            <span v-if="saving === tmpl.id" class="spinner-border spinner-border-sm me-1"></span>
            Save
          </button>
        </div>
        <div class="card-body">
          <textarea
            v-model="tmpl.content"
            class="form-control font-monospace"
            rows="10"
            :placeholder="`HTML content for ${tmpl.name} page`"
          ></textarea>
        </div>
      </div>

      <p v-if="!templates.length" class="text-muted">No templates found.</p>
    </div>
  </AdminLayout>
</template>
