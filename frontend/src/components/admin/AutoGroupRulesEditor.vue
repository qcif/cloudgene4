<script setup>
import { computed, ref, watch } from 'vue'
import { updateAutoGroups, testAutoGroups } from '@/api/admin'
import { apiErrorMessage, apiFieldErrors } from '@/api/client'
import { validateEmail } from '@/utils/validation'
import AlertMessage from '@/components/common/AlertMessage.vue'

const props = defineProps({
  rules: { type: Array, default: () => [] },
  requireActivation: { type: Boolean, default: true },
  existingGroups: { type: Array, default: () => [] },
})
const emit = defineEmits(['saved', 'dirty'])

const ADMIN = 'admin'
const ROW_KEY = /^auto_groups\[(\d+)\]\.(pattern|groups)$/

const copy = (rules) => rules.map((r) => ({ pattern: r.pattern, groups: [...r.groups] }))

const rows = ref(copy(props.rules))
const baseline = ref(JSON.stringify(props.rules))
const rowErrors = ref({})
const error = ref('')
const success = ref(false)
const saving = ref(false)

const testEmail = ref('')
const testing = ref(false)
const testError = ref('')
const testResult = ref(null)

const dirty = computed(() => JSON.stringify(rows.value) !== baseline.value)
watch(dirty, (v) => emit('dirty', v), { immediate: true })

const groupOptions = computed(() =>
  props.existingGroups.map((g) => g.name).filter((n) => n.toLowerCase() !== ADMIN))
const isNew = (name) => !props.existingGroups.some((g) => g.name.toLowerCase() === name.toLowerCase())
const matched = (i) => !!testResult.value && testResult.value.matched_rules.includes(i)
const rowError = (i, key) => rowErrors.value[i]?.[key]?.[0] || ''

function resetMessages() {
  error.value = ''
  success.value = false
  rowErrors.value = {}
}

function edited() {
  testResult.value = null
  testError.value = ''
  success.value = false
}

function structural() {
  rowErrors.value = {}
  edited()
}

function collectRowErrors(fields) {
  const out = {}
  for (const [key, msgs] of Object.entries(fields)) {
    const m = ROW_KEY.exec(key)
    if (m) out[m[1]] = { ...out[m[1]], [m[2]]: msgs }
  }
  return out
}

function addRule() {
  rows.value.push({ pattern: '', groups: [] })
  structural()
}

function removeRule(i) {
  rows.value.splice(i, 1)
  structural()
}

function move(i, delta) {
  const j = i + delta
  if (j < 0 || j >= rows.value.length) return
  const list = rows.value
  ;[list[i], list[j]] = [list[j], list[i]]
  structural()
}

function addGroup(i, name) {
  if (!name) return
  const groups = rows.value[i].groups
  if (!groups.some((g) => g.toLowerCase() === name.toLowerCase())) groups.push(name)
  rowErrors.value = { ...rowErrors.value, [i]: { ...rowErrors.value[i], groups: undefined } }
  edited()
}

const availableGroups = (rule) => groupOptions.value.filter(
  (n) => !rule.groups.some((g) => g.toLowerCase() === n.toLowerCase()))

function removeGroup(i, name) {
  rows.value[i].groups = rows.value[i].groups.filter((g) => g !== name)
  edited()
}

async function save() {
  resetMessages()
  saving.value = true
  try {
    const { data } = await updateAutoGroups(rows.value)
    rows.value = copy(data.auto_groups)
    baseline.value = JSON.stringify(data.auto_groups)
    structural()
    success.value = true
    emit('saved', data)
  } catch (e) {
    error.value = apiErrorMessage(e, 'Saving the rules failed.')
    rowErrors.value = collectRowErrors(apiFieldErrors(e))
  } finally {
    saving.value = false
  }
}

async function runTest() {
  testError.value = ''
  testResult.value = null
  const msg = validateEmail(testEmail.value)
  if (msg) {
    testError.value = msg
    return
  }
  rowErrors.value = {}
  testing.value = true
  try {
    const { data } = await testAutoGroups(testEmail.value, dirty.value ? rows.value : undefined)
    testResult.value = data
  } catch (e) {
    const fields = apiFieldErrors(e)
    rowErrors.value = collectRowErrors(fields)
    testError.value = fields.email?.[0]
      || (Object.keys(rowErrors.value).length ? '' : apiErrorMessage(e, 'The test failed.'))
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div data-testid="auto-rules-editor">
    <div class="alert alert-info small" data-testid="auto-rules-info">
      <i class="fas fa-info-circle me-1"></i>
      Users join these groups when they activate their account from the e-mail link, if their
      address fully matches the pattern. Existing members are not changed. Patterns are
      case-insensitive; write <code>.*@example\.org</code>.
    </div>
    <div v-if="!requireActivation" class="alert alert-warning small" data-testid="auto-rules-activation-off">
      <i class="fas fa-exclamation-triangle me-1"></i>
      Account activation is off, so these rules never apply.
    </div>
    <AlertMessage :message="error" data-testid="auto-rules-error" />
    <div v-if="success" class="alert alert-success py-2" data-testid="auto-rules-success">Rules saved.</div>

    <p v-if="!rows.length" class="text-muted" data-testid="auto-rules-empty">No automatic membership rules.</p>
    <table v-else class="table table-sm align-top">
      <thead>
        <tr><th>#</th><th>Pattern (regex)</th><th>Groups</th><th></th></tr>
      </thead>
      <tbody>
        <tr
          v-for="(rule, i) in rows"
          :key="i"
          :class="{ 'table-success': matched(i) }"
          :data-matched="matched(i) ? 'true' : 'false'"
          data-testid="auto-rule-row"
        >
          <td class="text-muted">{{ i + 1 }}</td>
          <td style="min-width: 14rem;">
            <input
              v-model="rule.pattern"
              type="text"
              :class="['form-control form-control-sm font-monospace', rowError(i, 'pattern') ? 'is-invalid' : '']"
              :aria-label="`Pattern for rule ${i + 1}`"
              data-testid="auto-rule-pattern"
              @input="edited"
            />
            <div class="invalid-feedback" data-testid="auto-rule-pattern-error">{{ rowError(i, 'pattern') }}</div>
            <div v-if="!rule.pattern.trim()" class="form-text text-warning" data-testid="auto-rule-inert">
              This rule never matches; fix or remove it.
            </div>
          </td>
          <td style="min-width: 16rem;">
            <span
              v-for="name in rule.groups"
              :key="name"
              class="badge bg-secondary me-1 mb-1"
              data-testid="auto-rule-group"
            >
              {{ name }}
              <span v-if="isNew(name)" class="badge bg-info text-dark ms-1" data-testid="auto-rule-group-new">new</span>
              <button
                type="button"
                class="btn-close btn-close-white ms-1"
                style="font-size: 0.5rem;"
                :aria-label="`Remove ${name}`"
                data-testid="auto-rule-group-remove"
                @click="removeGroup(i, name)"
              ></button>
            </span>
            <select
              :class="['form-select form-select-sm w-auto', rowError(i, 'groups') ? 'is-invalid' : '']"
              :aria-label="`Add group to rule ${i + 1}`"
              data-testid="auto-rule-group-add"
              @change="addGroup(i, $event.target.value); $event.target.value = ''"
            >
              <option value="">+ group</option>
              <option v-for="name in availableGroups(rule)" :key="name" :value="name">{{ name }}</option>
            </select>
            <div class="invalid-feedback d-block" data-testid="auto-rule-groups-error">{{ rowError(i, 'groups') }}</div>
          </td>
          <td class="text-end text-nowrap">
            <button type="button" class="btn btn-sm btn-link" title="Up" aria-label="Move up" :disabled="i === 0" data-testid="auto-rule-up" @click="move(i, -1)"><i class="fas fa-arrow-up"></i></button>
            <button type="button" class="btn btn-sm btn-link" title="Down" aria-label="Move down" :disabled="i === rows.length - 1" data-testid="auto-rule-down" @click="move(i, 1)"><i class="fas fa-arrow-down"></i></button>
            <button type="button" class="btn btn-sm btn-link text-danger" title="Remove" aria-label="Remove rule" data-testid="auto-rule-remove" @click="removeRule(i)"><i class="fas fa-trash"></i></button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="d-flex justify-content-between mb-4">
      <button type="button" class="btn btn-outline-secondary btn-sm" data-testid="auto-rule-add" @click="addRule">
        <i class="fas fa-plus"></i> Add rule
      </button>
      <button type="button" class="btn btn-primary btn-sm" :disabled="saving" data-testid="auto-rules-save" @click="save">
        <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>Save rules
      </button>
    </div>

    <form novalidate data-testid="auto-test-form" @submit.prevent="runTest">
      <label class="form-label" for="auto-test-email">Test email</label>
      <div class="input-group">
        <input
          id="auto-test-email"
          v-model="testEmail"
          type="text"
          :class="['form-control', testError ? 'is-invalid' : '']"
          placeholder="jo@example.org"
          data-testid="auto-test-email"
          @input="testResult = null"
        />
        <button type="submit" class="btn btn-outline-primary" :disabled="testing" data-testid="auto-test-submit">
          <span v-if="testing" class="spinner-border spinner-border-sm me-1"></span>Test
        </button>
        <div class="invalid-feedback" data-testid="auto-test-error">{{ testError }}</div>
      </div>
    </form>
    <div v-if="testResult" class="mt-2" data-testid="auto-test-result">
      <template v-if="testResult.matched_rules.length">
        Matches {{ testResult.matched_rules.length === 1 ? 'rule' : 'rules' }}
        {{ testResult.matched_rules.map((i) => i + 1).join(', ') }}.
        <span v-if="testResult.groups.length">Joins: {{ testResult.groups.join(', ') }}</span>
        <span v-else>No groups would be added.</span>
      </template>
      <template v-else>No rule matches this address.</template>
    </div>
  </div>
</template>
