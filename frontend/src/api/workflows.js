import client from './client'

export const listWorkflows = () =>
  client.get('/workflows/')

export const getWorkflow = (id) =>
  client.get(`/workflows/${id}/`)

export const listCategories = () =>
  client.get('/categories/')
