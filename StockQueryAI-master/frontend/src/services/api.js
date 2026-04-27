import axios from 'axios'

// API instance with default configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

// Handle responses and errors
api.interceptors.response.use((response) => {
  return response
}, (error) => {
  // If 401, token is invalid or expired
  if (error.response?.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('email')
    localStorage.removeItem('user')
    // Optionally redirect to login
    window.location.href = '/'
  }
  return Promise.reject(error)
})

export default api
