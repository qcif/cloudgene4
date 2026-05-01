<script setup>
import { ref, onMounted } from 'vue'
import { listJobs, cancelJob } from '@/api/jobs'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import JobStatusBadge from '@/components/jobs/JobStatusBadge.vue'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const jobs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(true)
const statusFilter = ref('')
const confirmJob = ref(null)
const confirmLoading = ref(false)

const totalPages = () => Math.ceil(total.value / pageSize)

function prettyDate(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleString()
}

async function fetchJobs(page = 1) {
  loading.value = true
  try {
    const params = { page }
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await listJobs(page)
    jobs.value = data.results ?? data
    total.value = data.count ?? jobs.value.length
    currentPage.value = page
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchJobs())

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
  <AdminLayout>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="mb-0">Jobs</h2>
      <select v-model="statusFilter" class="form-select w-auto" @change="fetchJobs(1)">
        <option value="">All statuses</option>
        <option value="running">Running</option>
        <option value="pending">Pending</option>
        <option value="waiting">Waiting</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
        <option value="cancelled">Cancelled</option>
      </select>
    </div>

    <LoadingSpinner v-if="loading" />

    <template v-else>
      <div class="card mb-3">
        <div class="card-body p-0">
          <table class="table table-sm table-hover mb-0">
            <thead>
              <tr>
                <th>Status</th>
                <th>Name</th>
                <th>Workflow</th>
                <th>User</th>
                <th>Submitted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in jobs" :key="job.id">
                <td><JobStatusBadge :status="job.status" /></td>
                <td>
                  <RouterLink :to="`/jobs/${job.id}`">{{ job.name }}</RouterLink>
                </td>
                <td><small>{{ job.workflow_id }}</small></td>
                <td><small>{{ job.username }}</small></td>
                <td><small>{{ prettyDate(job.submitted_at) }}</small></td>
                <td>
                  <button
                    v-if="['running','pending','waiting'].includes(job.status)"
                    class="btn btn-sm btn-outline-warning"
                    @click="confirmJob = job"
                  >
                    <i class="fas fa-times"></i> Cancel
                  </button>
                </td>
              </tr>
              <tr v-if="!jobs.length">
                <td colspan="6" class="text-muted text-center">No jobs found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages()"
        @change="fetchJobs"
      />
    </template>

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
  </AdminLayout>
</template>
