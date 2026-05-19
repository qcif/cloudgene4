import client from './client'

export const getDashboard = () =>
  client.get('/admin/dashboard/')

export const getServerSettings = () =>
  client.get('/admin/server-settings/')

export const updateServerSettings = (data) =>
  client.post('/admin/server-settings/', data)

export const getTemplates = () =>
  client.get('/admin/templates/')

export const updateTemplate = (id, data) =>
  client.patch(`/admin/templates/${id}/`, data)

export const getNavbarItems = () =>
  client.get('/admin/navbar-items/')

export const getSystemLogs = (params = {}) =>
  client.get('/admin/system-logs/', { params })

export const getCounters = () =>
  client.get('/admin/counters/')

export const getWorkflowSettings = (workflowId) =>
  client.get(`/admin/workflows/${workflowId}/settings/`)

export const updateWorkflowSettings = (workflowId, data) =>
  client.patch(`/admin/workflows/${workflowId}/settings/`, data)
