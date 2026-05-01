import { defineStore } from 'pinia'
import { listJobs, getJob } from '@/api/jobs'

export const useJobsStore = defineStore('jobs', {
  state: () => ({
    jobs: [],
    total: 0,
    currentPage: 1,
  }),

  actions: {
    async fetchJobs(page = 1) {
      const { data } = await listJobs(page)
      this.jobs = data.results ?? data
      this.total = data.count ?? data.length
      this.currentPage = page
    },

    async refreshJob(id) {
      const { data } = await getJob(id)
      const idx = this.jobs.findIndex((j) => j.id === id)
      if (idx !== -1) this.jobs[idx] = data
      return data
    },
  },
})
