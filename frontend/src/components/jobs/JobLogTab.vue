<script setup>
import { ref, onMounted } from 'vue'
import { getJobLogs } from '@/api/jobs'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const props = defineProps({ jobId: { type: String, required: true } })

const logs = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await getJobLogs(props.jobId)
    logs.value = typeof data === 'string' ? data : data.logs || JSON.stringify(data)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <LoadingSpinner v-if="loading" />
  <div v-else>
    <div class="d-flex justify-content-between align-items-center mb-2">
      <strong>Logs</strong>
      <a :href="`/api/jobs/${jobId}/logs/`" class="btn btn-sm btn-outline-secondary" download>
        <i class="fas fa-download me-1"></i>Download
      </a>
    </div>
    <div class="log-output">{{ logs || 'No log output available.' }}</div>
  </div>
</template>
