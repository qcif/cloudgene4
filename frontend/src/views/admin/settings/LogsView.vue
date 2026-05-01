<script setup>
import { ref, onMounted } from 'vue'
import { getSystemLogs } from '@/api/admin'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Pagination from '@/components/common/Pagination.vue'

const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 50
const loading = ref(true)
const levelFilter = ref('')
const componentFilter = ref('')

const totalPages = () => Math.ceil(total.value / pageSize)

const levelClass = {
  ERROR: 'text-danger',
  WARNING: 'text-warning',
  INFO: 'text-info',
  DEBUG: 'text-secondary',
}

async function fetchLogs(page = 1) {
  loading.value = true
  try {
    const params = { page }
    if (levelFilter.value) params.level = levelFilter.value
    if (componentFilter.value) params.component = componentFilter.value
    const { data } = await getSystemLogs(params)
    logs.value = data.results ?? data
    total.value = data.count ?? logs.value.length
    currentPage.value = page
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchLogs())
</script>

<template>
  <AdminLayout>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="mb-0">System Logs</h2>
      <div class="d-flex gap-2">
        <select v-model="levelFilter" class="form-select form-select-sm" @change="fetchLogs(1)">
          <option value="">All levels</option>
          <option>DEBUG</option>
          <option>INFO</option>
          <option>WARNING</option>
          <option>ERROR</option>
        </select>
        <input
          v-model="componentFilter"
          type="text"
          class="form-control form-control-sm"
          placeholder="Component…"
          @keyup.enter="fetchLogs(1)"
        />
        <button class="btn btn-sm btn-outline-secondary" @click="fetchLogs(1)">
          <i class="fas fa-filter"></i>
        </button>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />

    <template v-else>
      <div class="card mb-3">
        <div class="card-body p-0">
          <table class="table table-sm table-hover font-monospace mb-0" style="font-size: 0.8rem;">
            <thead>
              <tr>
                <th>Time</th>
                <th>Level</th>
                <th>Component</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id">
                <td class="text-muted text-nowrap">{{ new Date(log.created_at).toLocaleString() }}</td>
                <td :class="levelClass[log.level] || ''"><strong>{{ log.level }}</strong></td>
                <td>{{ log.component }}</td>
                <td>{{ log.message }}</td>
              </tr>
              <tr v-if="!logs.length">
                <td colspan="4" class="text-muted text-center">No log entries found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages()"
        @change="fetchLogs"
      />
    </template>
  </AdminLayout>
</template>
