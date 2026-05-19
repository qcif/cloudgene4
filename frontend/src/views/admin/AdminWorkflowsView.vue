<script setup>
import { ref, onMounted } from 'vue'
import { listWorkflows } from '@/api/workflows'
import { listGroups, updateUser } from '@/api/users'
import { updateWorkflowSettings } from '@/api/admin'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import AlertMessage from '@/components/common/AlertMessage.vue'

const workflows = ref([])
const groups = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')

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

const toggleWorkflowGroup = async (workflow, groupName) => {
  const current = workflow.allowed_groups ?? []
  const isCurrentlyAllowed = current.some(g => g === groupName || g.name === groupName)
  
  try {
    error.value = ''
    success.value = ''
    
    // Determine new group list
    let newGroupNames
    if (isCurrentlyAllowed) {
      // Remove the group
      newGroupNames = current
        .filter(g => g !== groupName && g.name !== groupName)
        .map(g => typeof g === 'string' ? g : g.name)
    } else {
      // Add the group
      newGroupNames = [
        ...current.map(g => typeof g === 'string' ? g : g.name),
        groupName
      ]
    }
    
    // Update via API
    const response = await updateWorkflowSettings(workflow.id, {
      allowed_group_names: newGroupNames
    })
    
    // Update local state with the response
    workflow.allowed_groups = response.data.allowed_groups || newGroupNames
    
    success.value = `Group ${isCurrentlyAllowed ? 'removed from' : 'added to'} ${workflow.name}`
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to update workflow group membership'
  }
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
                <div v-if="wf.public" class="d-flex align-items-center gap-2">
                  <span class="badge bg-info">Public</span>
                  <small class="text-muted">(All users)</small>
                </div>
                <div v-else class="d-flex align-items-center gap-1 flex-wrap">
                  <div v-for="g in groups" :key="g.id" class="form-check form-check-inline mb-1" v-if="g && g.id">
                    <input
                      type="checkbox"
                      class="form-check-input"
                      :id="`wf-${wf.id}-${g.id}`"
                      :checked="(wf.allowed_groups ?? []).some(ag => ag === g.name || (ag.name && ag.name === g.name))"
                      @change="toggleWorkflowGroup(wf, g.name)"
                    />
                    <label :for="`wf-${wf.id}-${g.id}`" class="form-check-label small">
                      {{ g.name }}
                    </label>
                  </div>
                  <span v-if="!groups.length" class="badge bg-light text-dark">No groups available</span>
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
  </AdminLayout>
</template>
