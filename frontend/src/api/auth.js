import client from './client'

export const login = (username, password) =>
  client.post('/auth/login/', { username, password })

export const logout = () =>
  client.post('/auth/logout/')

export const register = (data) =>
  client.post('/auth/register/', data)

export const getToken = () =>
  client.get('/auth/token/')

export const activate = (activationKey) =>
  client.get(`/auth/activate/${activationKey}/`)

export const requestPasswordReset = (email) =>
  client.post('/auth/password-reset/', { email })

export const confirmPasswordReset = (token, password) =>
  client.post(`/auth/password-reset-confirm/${token}/`, { password })
