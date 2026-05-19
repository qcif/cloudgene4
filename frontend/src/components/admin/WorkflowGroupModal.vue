<template>
  <div class="modal fade show" style="display: block; background-color: rgba(0, 0, 0, 0.5);" @click="closeIfBackdrop">
    <div class="modal-dialog modal-md">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-users me-2"></i>
            Group Access for "{{ workflow.name }}"
          </h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        
        <div class="modal-body">
          <AlertMessage :message="error" />
          
          <div v-if="success" class="alert alert-success">
            {{ success }}
          </div>
          
          <!-- Public Access Toggle -->
          <div class="card mb-4">
            <div class="card-body">
              <div class="form-check form-switch">
                <input
                  class="form-check-input"
                  type="checkbox"
                  id="publicAccess"
                  :checked="workflow.public"
                  @change="togglePublicAccess"
                  :disabled="updating"
                />
                <label class="form-check-label fw-medium" for="publicAccess">
                  Public Access
                </label>
                <div class="form-text">
                  When enabled, all users can access this workflow. When disabled, only selected groups can access it.
                </div>
              </div>
            </div>
          </div>
          
          <!-- Group Selection (only shown if not public) -->
          <div v-if="!workflow.public" class="card">
            <div class="card-header">
              <h6 class="mb-0">Allowed Groups</h6>
            </div>
            <div class="card-body">
              <div v-if="availableGroups.length" class="list-group">
                <div 
                  v-for="group in availableGroups" 
                  :key="group.id"
                  class="list-group-item d-flex justify-content-between align-items-center"
                >
                  <div class="form-check">
                    <input
                      type="checkbox"
                      class="form-check-input"
                      :id="`group-${group.id}`"
                      :checked="isGroupAssigned(group.name)"
                      @change="toggleGroup(group.name)"
                      :disabled="updating"
                    />
                    <label :for="`group-${group.id}`" class="form-check-label fw-medium">
                      {{ group.name }}
                    </label>
                  </div>
                  <span v-if="isGroupAssigned(group.name)" class="badge bg-success">
                    <i class="fas fa-check"></i>
                  </span>
                </div>
              </div>
              <div v-else class="text-muted text-center py-3">
                No groups available. Create groups in the Users admin page.
              </div>
            </div>
          </div>
          
          <!-- Current Status Summary -->
          <div class="mt-3">
            <small class="text-muted">
              <strong>Current access:</strong>
              <span v-if="workflow.public" class="text-info">
                Public (all users)
              </span>
              <span v-else-if="assignedGroups.length === 0" class="text-warning">
                No access (no groups assigned)
              </span>
              <span v-else class="text-success">
                {{ assignedGroups.length }} group{{ assignedGroups.length !== 1 ? 's' : '' }}
                ({{ assignedGroups.join(', ') }})
              </span>
            </small>
          </div>
        </div>
        
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')" :disabled="updating">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { updateWorkflowSettings } from '@/api/admin'
import AlertMessage from '@/components/common/AlertMessage.vue'

const props = defineProps({
  workflow: {
    type: Object,
    required: true
  },
  availableGroups: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'updated'])

const updating = ref(false)
const error = ref('')
const success = ref('')

const assignedGroups = computed(() => {
  const groups = props.workflow.allowed_groups || []
  return groups.map(g => typeof g === 'string' ? g : g.name || g)
})

const isGroupAssigned = (groupName) => {
  return assignedGroups.value.includes(groupName)
}

const closeIfBackdrop = (event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

const togglePublicAccess = async () => {
  updating.value = true
  error.value = ''
  success.value = ''
  
  try {
    const response = await updateWorkflowSettings(props.workflow.id, {
      public: !props.workflow.public
    })
    
    // Update local workflow object
    props.workflow.public = response.data.public
    
    success.value = `Workflow is now ${response.data.public ? 'public' : 'restricted to groups'}`
    emit('updated')
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      success.value = ''
    }, 3000)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to update public access'
  } finally {
    updating.value = false
  }
}

const toggleGroup = async (groupName) => {
  updating.value = true
  error.value = ''
  success.value = ''
  
  try {
    const currentGroups = assignedGroups.value
    const isCurrentlyAssigned = currentGroups.includes(groupName)
    
    let newGroupNames
    if (isCurrentlyAssigned) {
      newGroupNames = currentGroups.filter(g => g !== groupName)
    } else {
      newGroupNames = [...currentGroups, groupName]
    }
    
    const response = await updateWorkflowSettings(props.workflow.id, {
      allowed_group_names: newGroupNames
    })
    
    // Update local workflow object
    props.workflow.allowed_groups = response.data.allowed_groups || newGroupNames
    
    success.value = `${isCurrentlyAssigned ? 'Removed' : 'Added'} group "${groupName}"`
    emit('updated')
    
    // Clear success message after 2 seconds
    setTimeout(() => {
      success.value = ''
    }, 2000)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to update group assignment'
  } finally {
    updating.value = false
  }
}
</script>