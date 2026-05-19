<script setup>
import { ref, onMounted } from 'vue'
import { listWorkflows } from '@/api/workflows'
import { listGroups } from '@/api/users'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import AlertMessage from '@/components/common/AlertMessage.vue'
import WorkflowGroupModal from '@/components/admin/WorkflowGroupModal.vue'

const workflows = ref([])
const groups = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const selectedWorkflow = ref(null)

const statusBadge = { enabled: 'success', disabled: 'secondary', maintenance: 'warning' }

onMounted(async () => {
  try {
    const [workflowsRes, groupsRes] = await Promise.all([
      listWorkflows(),
      listGroups()
    ])
    workflows.value = workflowsRes.data.results ?? workflowsRes.data
    groups.value = groupsRes.data.results ?? groupsRes.data ?? []
  } catch (err) {
    error.value = 'Failed to load workflows or groups'
  } finally {
    loading.value = false
  }
})

const openGroupModal = (workflow) => {
  selectedWorkflow.value = workflow
}

const handleWorkflowUpdated = () => {
  // Refresh workflows to get updated data
  // In a full implementation, you might want to refresh the list
  success.value = 'Workflow access updated successfully'
  setTimeout(() => {
    success.value = ''
  }, 3000)
}

const getAssignedGroupNames = (workflow) => {
  const groups = workflow.allowed_groups || []
  return groups.map(g => typeof g === 'string' ? g : g.name || g)
}

const getGroupCount = (workflow) => {
  return getAssignedGroupNames(workflow).length
}
</script>

<template>
  <AdminLayout>
    <h2 class="mb-4">Workflows</h2>

    <AlertMessage :message="error" />
    <div v-if="success" class="alert alert-success">{{ success }}</div>

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
              <th>Group Access</th>
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
                <div class="d-flex align-items-center gap-2">
                  <div v-if="wf.public">
                    <span class="badge bg-info">Public</span>
                    <small class="text-muted ms-2">(All users)</small>
                  </div>
                  <div v-else class="d-flex flex-column">
                    <button 
                      class="btn btn-sm btn-outline-primary d-flex align-items-center gap-2"
                      @click="openGroupModal(wf)"
                    >
                      <i class="fas fa-users"></i>
                      <span v-if="getGroupCount(wf) === 0" class="text-warning">
                        No groups
                      </span>
                      <span v-else>
                        {{ getGroupCount(wf) }} group{{ getGroupCount(wf) !== 1 ? 's' : '' }}
                      </span>
                    </button>
                    <div v-if="getGroupCount(wf) > 0" class="small text-muted mt-1">
                      {{ getAssignedGroupNames(wf).slice(0, 2).join(', ') }}{{ getGroupCount(wf) > 2 ? '...' : '' }}
                    </div>
                  </div>
                </div>
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
    
    <WorkflowGroupModal
      v-if="selectedWorkflow"
      :workflow="selectedWorkflow"
      :available-groups="groups"
      @close="selectedWorkflow = null"
      @updated="handleWorkflowUpdated"
    />
  </AdminLayout>
</template>
