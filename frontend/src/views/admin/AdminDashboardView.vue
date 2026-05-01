<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '@/api/admin'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const stats = ref(null)
const recentJobs = ref([])
const loading = ref(true)

function prettyDate(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString()
}

const statusClass = {
  running: 'primary',
  completed: 'success',
  failed: 'danger',
  cancelled: 'secondary',
  pending: 'warning',
  waiting: 'warning',
}

onMounted(async () => {
  try {
    const { data } = await getDashboard()
    stats.value = data
    recentJobs.value = data.recent_jobs ?? []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AdminLayout>
    <h2 class="mb-4">Dashboard</h2>

    <LoadingSpinner v-if="loading" />

    <template v-else-if="stats">
      <div class="row g-3 mb-4">
        <div class="col-sm-6 col-lg-3">
          <div class="card text-bg-primary">
            <div class="card-body">
              <div class="text-white-50 small">Total Users</div>
              <div class="fs-3 fw-bold">{{ stats.total_users ?? '-' }}</div>
            </div>
          </div>
        </div>
        <div class="col-sm-6 col-lg-3">
          <div class="card text-bg-success">
            <div class="card-body">
              <div class="text-white-50 small">Total Jobs</div>
              <div class="fs-3 fw-bold">{{ stats.total_jobs ?? '-' }}</div>
            </div>
          </div>
        </div>
        <div class="col-sm-6 col-lg-3">
          <div class="card text-bg-info">
            <div class="card-body">
              <div class="text-white-50 small">Running Jobs</div>
              <div class="fs-3 fw-bold">{{ stats.running_jobs ?? '-' }}</div>
            </div>
          </div>
        </div>
        <div class="col-sm-6 col-lg-3">
          <div class="card text-bg-warning">
            <div class="card-body">
              <div class="text-dark small">Queued Jobs</div>
              <div class="fs-3 fw-bold text-dark">{{ stats.waiting_jobs ?? '-' }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header">Recent Jobs</div>
        <div class="card-body p-0">
          <table class="table table-sm mb-0">
            <thead>
              <tr>
                <th>Name</th>
                <th>Workflow</th>
                <th>User</th>
                <th>Submitted</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in recentJobs" :key="job.id">
                <td>
                  <RouterLink :to="`/jobs/${job.id}`">{{ job.name }}</RouterLink>
                </td>
                <td><small>{{ job.workflow_id }}</small></td>
                <td><small>{{ job.username }}</small></td>
                <td><small>{{ prettyDate(job.submitted_at) }}</small></td>
                <td>
                  <span :class="`badge bg-${statusClass[job.status] || 'secondary'}`">
                    {{ job.status }}
                  </span>
                </td>
              </tr>
              <tr v-if="!recentJobs.length">
                <td colspan="5" class="text-muted text-center">No jobs yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </AdminLayout>
</template>
