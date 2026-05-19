<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getWorkflow } from '@/api/workflows'
import { listGroups } from '@/api/users'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import AlertMessage from '@/components/common/AlertMessage.vue'

const route = useRoute()
const workflow = ref(null)
const groups = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')

onMounted(async () => {
  try {
    const [wfRes, grpRes] = await Promise.all([
      getWorkflow(route.params.id),
      listGroups(),
    ])
    workflow.value = wfRes.data
    groups.value = grpRes.data?.results || grpRes.data || []
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load workflow settings'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <LoadingSpinner v-if="loading" />

    <template v-else-if="workflow">
      <h2 class="mb-1">{{ workflow.name }}</h2>
      <p class="text-muted mb-4"><code>{{ workflow.id }}</code> &mdash; v{{ workflow.version }}</p>

      <AlertMessage :message="error" />
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <div class="card mb-4">
        <div class="card-header">Details</div>
        <div class="card-body">
          <dl class="row mb-0">
            <dt class="col-sm-3">Status</dt>
            <dd class="col-sm-9">{{ workflow.status }}</dd>
            <dt class="col-sm-3">Public</dt>
            <dd class="col-sm-9">{{ workflow.public ? 'Yes' : 'No' }}</dd>
            <dt class="col-sm-3">Description</dt>
            <dd class="col-sm-9">{{ workflow.description || '-' }}</dd>
          </dl>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header">Allowed Groups</div>
        <div class="card-body">
          <div v-if="!groups.length" class="text-muted">No groups defined.</div>
          <div v-for="g in groups" :key="g?.id || 'unknown'" class="form-check" v-if="g">
            <input
              type="checkbox"
              class="form-check-input"
              :id="`g-${g.id}`"
              :checked="(workflow.allowed_groups ?? []).some((ag) => ag === g.name || ag.name === g.name)"
              disabled
            />
            <label :for="`g-${g.id}`" class="form-check-label">{{ g.name }}</label>
          </div>
          <small class="text-muted mt-2 d-block">
            Group permissions are managed via the Django API or YAML configuration.
          </small>
        </div>
      </div>

      <div class="card">
        <div class="card-header">Parameters</div>
        <div class="card-body p-0">
          <table class="table table-sm mb-0">
            <thead>
              <tr><th>ID</th><th>Label</th><th>Type</th><th>Direction</th><th>Required</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in workflow.parameters" :key="p.id">
                <td><code>{{ p.id }}</code></td>
                <td>{{ p.label }}</td>
                <td><small>{{ p.type }}</small></td>
                <td><small>{{ p.direction ?? 'input' }}</small></td>
                <td>{{ p.required ? 'Yes' : 'No' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <template v-else-if="error">
      <AlertMessage :message="error" />
    </template>

    <template v-else>
      <AlertMessage message="Workflow not found." />
    </template>
  </AdminLayout>
</template>
