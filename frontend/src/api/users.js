import client from './client'

export const listUsers = (params = {}) =>
  client.get('/users/', { params })

export const getUser = (id) =>
  client.get(`/users/${id}/`)

export const updateUser = (id, data) =>
  client.patch(`/users/${id}/`, data)

export const deleteUser = (id) =>
  client.delete(`/users/${id}/`)

export const listGroups = () =>
  client.get('/groups/')
