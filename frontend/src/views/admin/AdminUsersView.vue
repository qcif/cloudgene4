<script setup>
import { ref, onMounted } from 'vue'
import { listUsers, deleteUser, updateUser, listGroups } from '@/api/users'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import AlertMessage from '@/components/common/AlertMessage.vue'
import GroupManagementModal from '@/components/admin/GroupManagementModal.vue'

const users = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(true)
const search = ref('')
const groups = ref([])

const confirmUser = ref(null)
const confirmLoading = ref(false)
const error = ref('')
const showGroupModal = ref(false)

const totalPages = () => Math.ceil(total.value / pageSize)

// md5 gravatar URL — use a simple hash approximation via DiceBear as fallback
function avatarUrl(email) {
  return `https://www.gravatar.com/avatar/${email}?d=identicon&s=32`
}

async function fetchUsers(page = 1) {
  loading.value = true
  try {
    const params = { page }
    if (search.value) params.search = search.value
    const { data } = await listUsers(params)
    users.value = data.results ?? data
    total.value = data.count ?? users.value.length
    currentPage.value = page
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchUsers(), listGroups().then((r) => { groups.value = r.data.results || [] })])
})

async function doDelete() {
  confirmLoading.value = true
  try {
    await deleteUser(confirmUser.value.id)
    await fetchUsers(currentPage.value)
  } catch (e) {
    error.value = e.response?.data?.message || 'Delete failed.'
  } finally {
    confirmLoading.value = false
    confirmUser.value = null
  }
}

async function toggleGroup(user, groupName) {
  const current = user.groups ?? []
  const updated = current.includes(groupName)
    ? current.filter((g) => g !== groupName)
    : [...current, groupName]
  try {
    await updateUser(user.id, { groups: updated })
    user.groups = updated
  } catch (e) {
    error.value = 'Group update failed.'
  }
}

async function refreshGroups() {
  try {
    const response = await listGroups()
    groups.value = response.data.results || []
  } catch (e) {
    console.error('Failed to refresh groups:', e)
  }
}

function handleGroupsUpdated() {
  // Refresh both groups and users to get updated membership
  Promise.all([refreshGroups(), fetchUsers(currentPage.value)])
}
</script>

<template>
  <AdminLayout>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="mb-0">Users</h2>
      <div class="input-group w-auto">
        <input
          v-model="search"
          type="text"
          class="form-control"
          placeholder="Search users…"
          @keyup.enter="fetchUsers(1)"
        />
        <button class="btn btn-outline-secondary" @click="fetchUsers(1)">
          <i class="fas fa-search"></i>
        </button>
      </div>
    </div>

    <AlertMessage :message="error" />
    <LoadingSpinner v-if="loading" />

    <template v-else>
      <div class="card mb-3">
        <div class="card-body p-0">
          <table class="table table-sm table-hover mb-0 align-middle">
            <thead>
              <tr>
                <th></th>
                <th>Username</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Last Login</th>
                <th>Groups</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>
                  <img :src="avatarUrl(user.email)" class="rounded-circle" width="32" height="32" />
                </td>
                <td>{{ user.username }}</td>
                <td>{{ user.full_name }}</td>
                <td><small>{{ user.email }}</small></td>
                <td><small>{{ user.last_login ? new Date(user.last_login).toLocaleDateString() : '-' }}</small></td>
                <td>
                  <div class="d-flex align-items-center gap-2">
                    <div v-for="g in groups" :key="g.id" class="form-check form-check-inline" v-if="g && g.id">
                      <input
                        type="checkbox"
                        class="form-check-input"
                        :id="`g-${user.id}-${g.id}`"
                        :checked="(user.groups ?? []).includes(g.name)"
                        @change="toggleGroup(user, g.name)"
                      />
                      <label :for="`g-${user.id}-${g.id}`" class="form-check-label small">
                        {{ g.name }}
                      </label>
                    </div>
                    <button
                      class="btn btn-sm btn-outline-primary ms-2"
                      @click="showGroupModal = true"
                      title="Manage groups"
                    >
                      <i class="fas fa-cog"></i>
                    </button>
                  </div>
                </td>
                <td>
                  <button
                    class="btn btn-sm btn-outline-danger"
                    title="Delete user"
                    @click="confirmUser = user"
                  >
                    <i class="fas fa-trash"></i>
                  </button>
                </td>
              </tr>
              <tr v-if="!users.length">
                <td colspan="7" class="text-muted text-center">No users found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages()"
        @change="fetchUsers"
      />
    </template>

    <ConfirmDialog
      v-if="confirmUser"
      title="Delete User"
      :message="`Are you sure you want to delete <b>${confirmUser.username}</b>? This cannot be undone.`"
      confirm-text="Delete"
      :loading="confirmLoading"
      @confirm="doDelete"
      @cancel="confirmUser = null"
    />
    
    <GroupManagementModal
      v-if="showGroupModal"
      :show="showGroupModal"
      :users="users"
      :initial-groups="groups"
      @close="showGroupModal = false"
      @groups-updated="handleGroupsUpdated"
    />
  </AdminLayout>
</template>
