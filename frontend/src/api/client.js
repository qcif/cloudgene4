import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
})

client.interceptors.request.use((config) => {
  // Auto-detect content type based on data
  if (config.data instanceof FormData) {
    // Let axios handle FormData content-type with boundary
    delete config.headers['Content-Type']
  } else if (config.data && typeof config.data === 'object') {
    // Set JSON content-type for object data
    config.headers['Content-Type'] = 'application/json'
  }
  
  const token = localStorage.getItem('cg_token')
  if (token) {
    config.headers['Authorization'] = `Token ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cg_token')
      localStorage.removeItem('cg_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
