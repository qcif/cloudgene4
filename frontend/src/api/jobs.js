import client from './client'

export const listJobs = (page = 1) =>
  client.get('/jobs/', { params: { page } })

export const getJob = (id) =>
  client.get(`/jobs/${id}/`)

export const submitJob = (data) =>
  client.post('/jobs/', data, { headers: { 'Content-Type': 'multipart/form-data' } })

export const cancelJob = (id) =>
  client.post(`/jobs/${id}/cancel/`)

export const restartJob = (id) =>
  client.post(`/jobs/${id}/restart/`)

export const getJobLogs = (id) =>
  client.get(`/jobs/${id}/logs/`)

export const listDownloads = (id) =>
  client.get(`/jobs/${id}/download/`)

export const getQueueStatus = () =>
  client.get('/jobs/queue_status/')

export const pauseQueue = () =>
  client.post('/jobs/pause_queue/')

export const resumeQueue = () =>
  client.post('/jobs/resume_queue/')
