<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { listJobs, cancelJob } from '@/api/jobs'
import JobStatusBadge from '@/components/jobs/JobStatusBadge.vue'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const jobs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(true)

const confirmJob = ref(null)
const confirmLoading = ref(false)

let pollTimer = null

const totalPages = () => Math.ceil(total.value / pageSize)

function prettyDate(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString()
}

function prettyDuration(start, end) {
  if (!start || !end) return '-'
  const ms = new Date(end) - new Date(start)
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ${s % 60}s`
  return `${Math.floor(m / 60)}h ${m % 60}m`
}

const activeStates = new Set(['pending', 'waiting', 'running'])

async function fetchJobs(page = 1) {
  const { data } = await listJobs(page)
  jobs.value = data.results ?? data
  total.value = data.count ?? jobs.value.length
  currentPage.value = page
}

function scheduleRefresh() {
  const hasActive = jobs.value.some((j) => activeStates.has(j.status))
  if (hasActive) {
    pollTimer = setTimeout(async () => {
      await fetchJobs(currentPage.value)
      scheduleRefresh()
    }, 20000)
  }
}

onMounted(async () => {
  try {
    await fetchJobs(1)
    scheduleRefresh()
  } finally {
    loading.value = false
  }
})

onUnmounted(() => clearTimeout(pollTimer))

async function onPageChange(page) {
  loading.value = true
  try {
    await fetchJobs(page)
  } finally {
    loading.value = false
  }
}

async function doCancel() {
  confirmLoading.value = true
  try {
    await cancelJob(confirmJob.value.id)
    await fetchJobs(currentPage.value)
  } finally {
    confirmLoading.value = false
    confirmJob.value = null
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <div class="py-1 container">
        <h2>Jobs</h2>
        <span><b>{{ total }}</b> jobs submitted.</span>
      </div>
    </div>

    <div class="container">
      <LoadingSpinner v-if="loading" />

      <template v-else>
        <div
          v-for="job in jobs"
          :key="job.id"
          class="card card-shadow mb-3 mt-2"
          :class="`job-${job.status}`"
        >
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <JobStatusBadge :status="job.status" />
              <div class="flex-grow-1">
                <b><RouterLink :to="`/jobs/${job.id}`">{{ job.name }}</RouterLink></b><br>
                <small class="text-muted">
                  <i class="far fa-clock"></i> {{ prettyDate(job.submitted_at) }}&nbsp;&nbsp;
                  <i class="far fa-hourglass"></i> {{ prettyDuration(job.started_at, job.completed_at) }}&nbsp;&nbsp;
                  <i class="fas fa-tag"></i> {{ job.workflow_id }}
                </small>
              </div>
              <button
                v-if="job.status === 'running' || job.status === 'pending' || job.status === 'waiting'"
                class="btn btn-light btn-sm"
                title="Cancel job"
                @click="confirmJob = job"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
        </div>

        <p v-if="!jobs.length" class="text-muted mt-4">No jobs found.</p>

        <div class="mt-4">
          <Pagination
            :current-page="currentPage"
            :total-pages="totalPages()"
            @change="onPageChange"
          />
        </div>
      </template>
    </div>

    <ConfirmDialog
      v-if="confirmJob"
      title="Cancel Job"
      :message="`Are you sure you want to cancel <b>${confirmJob.name}</b>?`"
      confirm-text="Cancel Job"
      confirm-class="btn-warning"
      :loading="confirmLoading"
      @confirm="doCancel"
      @cancel="confirmJob = null"
    />
  </div>
</template>
