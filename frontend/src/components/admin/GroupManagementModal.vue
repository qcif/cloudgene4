<script setup>
import { computed, ref, onMounted } from 'vue'
import { getAutoGroups } from '@/api/admin'
import { createGroup, deleteGroup, listGroups } from '@/api/users'
import { apiErrorMessage, apiFieldErrors } from '@/api/client'
import { firstFieldErrors, validateGroupName } from '@/utils/validation'
import AlertMessage from '@/components/common/AlertMessage.vue'
import AutoGroupRulesEditor from './AutoGroupRulesEditor.vue'
import GroupMembersModal from './GroupMembersModal.vue'

defineProps({
  show: { type: Boolean, default: true },
})
const emit = defineEmits(['close', 'groups-updated'])

const PROTECTED = 'admin'

const groups = ref([])
const loading = ref(true)
const error = ref('')
const nameError = ref('')
const newGroupName = ref('')
const creating = ref(false)
const confirmDelete = ref(null)
const deleting = ref(false)
const selectedGroup = ref(null)

const UNSAVED_PROMPT = 'You have unsaved automatic membership rules. Discard them?'
const AUTO_DELETE_WARNING = ('Automatic membership rules name this group; it will be created again '
  + 'when a matching user activates.')
const tab = ref('groups')
const autoRules = ref([])
const requireActivation = ref(true)
const autoLoading = ref(true)
const autoError = ref('')
const rulesDirty = ref(false)

const autoNames = computed(() => new Set(
  autoRules.value.flatMap((r) => r.groups.map((g) => g.toLowerCase()))))
const isAuto = (group) => autoNames.value.has(group.name.toLowerCase())

async function loadAutoGroups() {
  autoLoading.value = true
  autoError.value = ''
  try {
    const { data } = await getAutoGroups()
    autoRules.value = data.auto_groups
    requireActivation.value = data.require_activation
  } catch (e) {
    autoError.value = apiErrorMessage(e, 'Could not load automatic membership rules.')
  } finally {
    autoLoading.value = false
  }
}

function rulesSaved(data) {
  autoRules.value = data.auto_groups
  requireActivation.value = data.require_activation
}

const discardOk = () => !rulesDirty.value || window.confirm(UNSAVED_PROMPT)

function switchTab(name) {
  if (name === tab.value) return
  if (tab.value === 'auto' && !discardOk()) return
  tab.value = name
  rulesDirty.value = false
}

function close() {
  if (discardOk()) emit('close')
}

async function refresh() {
  loading.value = true
  try {
    const { data } = await listGroups()
    groups.value = data
  } catch (e) {
    error.value = apiErrorMessage(e, 'Could not load groups.')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refresh()
  loadAutoGroups()
})

async function create() {
  error.value = ''
  nameError.value = validateGroupName(newGroupName.value) || ''
  if (nameError.value) return
  creating.value = true
  try {
    await createGroup({ name: newGroupName.value.trim() })
    newGroupName.value = ''
    await refresh()
    emit('groups-updated')
  } catch (e) {
    nameError.value = firstFieldErrors(apiFieldErrors(e)).name || ''
    if (!nameError.value) error.value = apiErrorMessage(e, 'Creating the group failed.')
  } finally {
    creating.value = false
  }
}

async function doDelete() {
  deleting.value = true
  error.value = ''
  try {
    await deleteGroup(confirmDelete.value.id)
    confirmDelete.value = null
    await refresh()
    emit('groups-updated')
  } catch (e) {
    error.value = apiErrorMessage(e, 'Deleting the group failed.')
    confirmDelete.value = null
  } finally {
    deleting.value = false
  }
}

function membersChanged() {
  refresh()
  emit('groups-updated')
}
</script>

<template>
  <div
    class="modal d-block"
    tabindex="-1"
    style="background: rgba(0,0,0,0.5);"
    data-testid="group-modal"
    @click.self="close()"
  >
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title"><i class="fas fa-users me-2"></i>Groups</h5>
          <button type="button" class="btn-close" aria-label="Close" data-testid="group-modal-close-x" @click="close()"></button>
        </div>

        <div class="modal-body">
          <ul class="nav nav-tabs mb-3" role="tablist">
            <li class="nav-item">
              <button
                type="button"
                :class="['nav-link', tab === 'groups' ? 'active' : '']"
                role="tab"
                data-testid="group-tab-groups"
                @click="switchTab('groups')"
              >Groups</button>
            </li>
            <li class="nav-item">
              <button
                type="button"
                :class="['nav-link', tab === 'auto' ? 'active' : '']"
                role="tab"
                data-testid="group-tab-auto"
                @click="switchTab('auto')"
              >Automatic membership</button>
            </li>
          </ul>

          <div v-if="tab === 'auto'">
            <div v-if="autoLoading" class="text-muted" data-testid="auto-rules-loading">
              <span class="spinner-border spinner-border-sm me-1"></span>Loading…
            </div>
            <AlertMessage v-else-if="autoError" :message="autoError" data-testid="auto-rules-load-error" />
            <AutoGroupRulesEditor
              v-else
              :rules="autoRules"
              :require-activation="requireActivation"
              :existing-groups="groups"
              @saved="rulesSaved"
              @dirty="rulesDirty = $event"
            />
          </div>

          <div v-show="tab === 'groups'">
          <p class="text-muted small">
            Groups control which workflows a user may run. Administrator rights are managed with the
            “Make admin” button in the user list, not through the <code>admin</code> group here.
          </p>
          <AlertMessage :message="error" data-testid="group-error" />

          <form class="d-flex gap-2 mb-4" novalidate data-testid="group-create-form" @submit.prevent="create">
            <div class="flex-grow-1">
              <input
                v-model="newGroupName"
                type="text"
                :class="['form-control', nameError ? 'is-invalid' : '']"
                placeholder="New group name, e.g. researchers"
                aria-label="New group name"
                :disabled="creating"
                data-testid="group-create-name"
              />
              <div class="invalid-feedback" data-testid="group-create-error">{{ nameError }}</div>
            </div>
            <div>
              <button type="submit" class="btn btn-primary text-nowrap" :disabled="creating" data-testid="group-create-submit">
                <span v-if="creating" class="spinner-border spinner-border-sm me-1"></span>
                Create group
              </button>
            </div>
          </form>

          <div v-if="loading" class="text-muted">Loading…</div>
          <table v-else-if="groups.length" class="table table-sm align-middle mb-0" data-testid="group-table">
            <thead>
              <tr>
                <th>Group</th>
                <th class="text-center">Members</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="group in groups" :key="group.id" data-testid="group-row" :data-group="group.name">
                <td>
                  <strong>{{ group.name }}</strong>
                  <span
                    v-if="isAuto(group)"
                    class="badge bg-info text-dark ms-2"
                    title="Named by an automatic membership rule"
                    data-testid="group-auto-badge"
                  >auto</span>
                </td>
                <td class="text-center">
                  <span class="badge bg-primary" data-testid="group-member-count">{{ group.member_count }}</span>
                </td>
                <td class="text-end text-nowrap">
                  <button
                    class="btn btn-sm btn-outline-primary me-2"
                    title="Members"
                    :aria-label="`Members of ${group.name}`"
                    data-testid="group-members"
                    @click="selectedGroup = group"
                  >
                    <i class="fas fa-users"></i>
                  </button>
                  <button
                    class="btn btn-sm btn-outline-danger"
                    :title="group.name === PROTECTED ? 'The admin group cannot be deleted' : 'Delete group'"
                    :aria-label="`Delete ${group.name}`"
                    :disabled="group.name === PROTECTED"
                    data-testid="group-delete"
                    @click="confirmDelete = group"
                  >
                    <i class="fas fa-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="text-center text-muted" data-testid="group-empty">No groups yet.</div>

          <div v-if="confirmDelete" class="alert alert-danger mt-3" data-testid="group-delete-dialog">
            Delete group <strong>{{ confirmDelete.name }}</strong>?
            Its {{ confirmDelete.member_count }} member(s) lose access to workflows restricted to it.
            <span v-if="isAuto(confirmDelete)" data-testid="group-delete-auto-warning">{{ AUTO_DELETE_WARNING }}</span>
            <div class="mt-2">
              <button class="btn btn-sm btn-danger me-2" :disabled="deleting" data-testid="group-delete-confirm" @click="doDelete">
                Delete
              </button>
              <button class="btn btn-sm btn-secondary" :disabled="deleting" data-testid="group-delete-cancel" @click="confirmDelete = null">
                Cancel
              </button>
            </div>
          </div>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-testid="group-modal-close" @click="close()">Close</button>
        </div>
      </div>
    </div>
  </div>

  <GroupMembersModal
    v-if="selectedGroup"
    :group="selectedGroup"
    @close="selectedGroup = null"
    @members-changed="membersChanged"
  />
</template>
