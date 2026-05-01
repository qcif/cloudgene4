<script setup>
import { ref, onMounted } from 'vue'
import { listWorkflows } from '@/api/workflows'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const workflows = ref([])
const loading = ref(true)

const statusBadge = { enabled: 'success', disabled: 'secondary', maintenance: 'warning' }

onMounted(async () => {
  try {
    const { data } = await listWorkflows()
    workflows.value = data.results ?? data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <h2 class="mb-4">Workflows</h2>

    <LoadingSpinner v-if="loading" />

    <div v-else class="card">
      <div class="card-body p-0">
        <table class="table table-sm table-hover mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Version</th>
              <th>Status</th>
              <th>Access</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="wf in workflows" :key="wf.id">
              <td><code>{{ wf.id }}</code></td>
              <td>{{ wf.name }}</td>
              <td><small>{{ wf.version }}</small></td>
              <td>
                <span :class="`badge bg-${statusBadge[wf.status] || 'secondary'}`">
                  {{ wf.status }}
                </span>
              </td>
              <td>
                <span v-if="wf.public" class="badge bg-info">Public</span>
                <span v-else class="badge bg-light text-dark">Groups only</span>
              </td>
              <td>
                <RouterLink :to="`/admin/workflows/${wf.id}`" class="btn btn-sm btn-outline-primary">
                  <i class="fas fa-cog"></i> Settings
                </RouterLink>
              </td>
            </tr>
            <tr v-if="!workflows.length">
              <td colspan="6" class="text-muted text-center">No workflows installed.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AdminLayout>
</template>
