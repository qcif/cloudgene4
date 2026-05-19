<template>
  <div class="modal fade show" style="display: block; background-color: rgba(0, 0, 0, 0.5);" @click="closeIfBackdrop">
    <div class="modal-dialog modal-md">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-users me-2"></i>
            Members of "{{ group.name }}"
          </h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        
        <div class="modal-body">
          <AlertMessage :message="error" />
          
          <div v-if="success" class="alert alert-success">
            {{ success }}
          </div>
          
          <!-- Current Members -->
          <div class="mb-4">
            <h6>Current Members ({{ groupMembers.length }})</h6>
            <div v-if="groupMembers.length" class="list-group">
              <div 
                v-for="user in groupMembers" 
                :key="user.id"
                class="list-group-item d-flex justify-content-between align-items-center"
              >
                <div class="d-flex align-items-center">
                  <img :src="avatarUrl(user.email)" class="rounded-circle me-2" width="24" height="24" />
                  <div>
                    <div class="fw-medium">{{ user.username }}</div>
                    <small class="text-muted">{{ user.email }}</small>
                  </div>
                </div>
                <button
                  class="btn btn-sm btn-outline-danger"
                  @click="removeFromGroup(user)"
                  title="Remove from group"
                  :disabled="updating"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
            <p v-else class="text-muted text-center py-3">
              No members in this group yet.
            </p>
          </div>
          
          <!-- Add Members -->
          <div>
            <h6>Add Members</h6>
            <div v-if="availableUsers.length" class="list-group">
              <div 
                v-for="user in availableUsers" 
                :key="user.id"
                class="list-group-item d-flex justify-content-between align-items-center"
              >
                <div class="d-flex align-items-center">
                  <img :src="avatarUrl(user.email)" class="rounded-circle me-2" width="24" height="24" />
                  <div>
                    <div class="fw-medium">{{ user.username }}</div>
                    <small class="text-muted">{{ user.email }}</small>
                  </div>
                </div>
                <button
                  class="btn btn-sm btn-outline-primary"
                  @click="addToGroup(user)"
                  title="Add to group"
                  :disabled="updating"
                >
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            </div>
            <p v-else class="text-muted text-center py-3">
              All users are already members of this group.
            </p>
          </div>
        </div>
        
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { updateUser } from '@/api/users'
import AlertMessage from '@/components/common/AlertMessage.vue'

const props = defineProps({
  group: {
    type: Object,
    required: true
  },
  users: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'update'])

const updating = ref(false)
const error = ref('')
const success = ref('')

const groupMembers = computed(() => {
  return props.users.filter(user => 
    (user.groups || []).includes(props.group.name)
  )
})

const availableUsers = computed(() => {
  return props.users.filter(user => 
    !(user.groups || []).includes(props.group.name)
  )
})

const avatarUrl = (email) => {
  return `https://www.gravatar.com/avatar/${email}?d=identicon&s=24`
}

const closeIfBackdrop = (event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

const addToGroup = async (user) => {
  updating.value = true
  error.value = ''
  success.value = ''
  
  try {
    const updatedGroups = [...(user.groups || []), props.group.name]
    await updateUser(user.id, { groups: updatedGroups })
    
    // Update local user object
    user.groups = updatedGroups
    
    success.value = `Added ${user.username} to ${props.group.name}`
    emit('update')
    
    // Clear success message after 2 seconds
    setTimeout(() => {
      success.value = ''
    }, 2000)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to add user to group'
  } finally {
    updating.value = false
  }
}

const removeFromGroup = async (user) => {
  updating.value = true
  error.value = ''
  success.value = ''
  
  try {
    const updatedGroups = (user.groups || []).filter(g => g !== props.group.name)
    await updateUser(user.id, { groups: updatedGroups })
    
    // Update local user object
    user.groups = updatedGroups
    
    success.value = `Removed ${user.username} from ${props.group.name}`
    emit('update')
    
    // Clear success message after 2 seconds
    setTimeout(() => {
      success.value = ''
    }, 2000)
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to remove user from group'
  } finally {
    updating.value = false
  }
}
</script>