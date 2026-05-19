<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getWorkflow } from '@/api/workflows'
import { getWorkflowSettings, updateWorkflowSettings } from '@/api/admin'
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
const saving = ref(false)
const formData = ref({
  nextflow_profile: '',
  working_directory: '',
  env_vars: '',
  nextflow_config: ''
})

onMounted(async () => {
  try {
    const [wfRes, settingsRes, grpRes] = await Promise.all([
      getWorkflow(route.params.id),
      getWorkflowSettings(route.params.id),
      listGroups(),
    ])
    workflow.value = wfRes.data
    groups.value = grpRes.data?.results || grpRes.data || []
    
    // Initialize form data from settings API
    const settings = settingsRes.data
    formData.value = {
      nextflow_profile: settings.nextflow_profile || '',
      working_directory: settings.working_directory || '',
      env_vars: settings.env_vars || '',
      nextflow_config: settings.nextflow_config || ''
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load workflow settings'
  } finally {
    loading.value = false
  }
})

const saveSettings = async () => {
  saving.value = true
  error.value = ''
  success.value = ''
  
  try {
    const response = await updateWorkflowSettings(route.params.id, formData.value)
    success.value = 'Settings saved successfully'
    
    // Update workflow data with the response
    const updatedSettings = response.data
    Object.assign(formData.value, {
      nextflow_profile: updatedSettings.nextflow_profile || '',
      working_directory: updatedSettings.working_directory || '',
      env_vars: updatedSettings.env_vars || '',
      nextflow_config: updatedSettings.nextflow_config || ''
    })
  } catch (err) {
    error.value = err.response?.data?.message || err.message || 'Failed to save settings'
  } finally {
    saving.value = false
  }
}

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

      <div class="card mb-4">
        <div class="card-header">Nextflow Configuration</div>
        <div class="card-body">
          <form @submit.prevent="saveSettings">
            <div class="mb-3">
              <label for="nextflow_profile" class="form-label">Nextflow Profile</label>
              <input
                type="text"
                class="form-control"
                id="nextflow_profile"
                v-model="formData.nextflow_profile"
                placeholder="e.g., docker, conda, local"
              />
              <div class="form-text">Nextflow profile to use for execution</div>
            </div>
            
            <div class="mb-3">
              <label for="working_directory" class="form-label">Working Directory</label>
              <input
                type="text"
                class="form-control"
                id="working_directory"
                v-model="formData.working_directory"
                placeholder="${CLOUDGENE_WORKSPACE_HOME}/work"
              />
              <div class="form-text">Working directory for Nextflow execution. Supports template variables with ${} syntax.</div>
            </div>
            
            <div class="mb-3">
              <label for="env_vars" class="form-label">Environment Variables</label>
              <textarea
                class="form-control"
                id="env_vars"
                v-model="formData.env_vars"
                rows="6"
                placeholder="SMTP_HOST=${CLOUDGENE_SMTP_HOST}\nAPP_NAME=${CLOUDGENE_APP_NAME}\nSERVICE_URL=${CLOUDGENE_SERVICE_URL}"
              ></textarea>
              <div class="form-text">Environment variables written to nextflow.env. Supports template variables with ${} syntax.</div>
            </div>
            
            <div class="mb-3">
              <label for="nextflow_config" class="form-label">Nextflow Configuration</label>
              <textarea
                class="form-control"
                id="nextflow_config"
                v-model="formData.nextflow_config"
                rows="8"
                placeholder="process {\n  executor = 'local'\n  cpus = 2\n  memory = '4 GB'\n}\n\nsingularity {\n  enabled = true\n  cacheDir = '${CLOUDGENE_WORKSPACE_HOME}/singularity'\n}"
              ></textarea>
              <div class="form-text">Nextflow configuration written to nextflow.config. Supports template variables with ${} syntax.</div>
            </div>
            
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              {{ saving ? 'Saving...' : 'Save Configuration' }}
            </button>
          </form>
        </div>
      </div>
      
      <div class="card mb-4">
        <div class="card-header">
          Available Template Variables
          <small class="text-muted ms-2">Use ${VARIABLE_NAME} syntax in configuration fields</small>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <h6>Application Settings</h6>
              <ul class="list-unstyled small">
                <li><code>${CLOUDGENE_APP_NAME}</code></li>
                <li><code>${CLOUDGENE_APP_ID}</code></li>
                <li><code>${CLOUDGENE_APP_VERSION}</code></li>
                <li><code>${CLOUDGENE_APP_LOCATION}</code></li>
                <li><code>${CLOUDGENE_SERVICE_NAME}</code></li>
                <li><code>${CLOUDGENE_SERVICE_URL}</code></li>
              </ul>
            </div>
            <div class="col-md-6">
              <h6>Infrastructure Settings</h6>
              <ul class="list-unstyled small">
                <li><code>${CLOUDGENE_WORKSPACE_TYPE}</code></li>
                <li><code>${CLOUDGENE_WORKSPACE_HOME}</code></li>
                <li><code>${CLOUDGENE_CONTACT_NAME}</code></li>
                <li><code>${CLOUDGENE_CONTACT_EMAIL}</code></li>
              </ul>
              
              <h6 class="mt-3">SMTP Settings</h6>
              <ul class="list-unstyled small">
                <li><code>${CLOUDGENE_SMTP_HOST}</code></li>
                <li><code>${CLOUDGENE_SMTP_PORT}</code></li>
                <li><code>${CLOUDGENE_SMTP_USER}</code></li>
                <li><code>${CLOUDGENE_SMTP_PASSWORD}</code></li>
                <li><code>${CLOUDGENE_SMTP_NAME}</code></li>
                <li><code>${CLOUDGENE_SMTP_SENDER}</code></li>
              </ul>
            </div>
          </div>
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
