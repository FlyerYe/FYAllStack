import axios from 'axios'

const request = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 5000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)

export default request