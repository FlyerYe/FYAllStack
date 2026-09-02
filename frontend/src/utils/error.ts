import axios from 'axios'

export function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    return (
      error.response?.data?.message ||
      error.response?.data?.detail ||
      '请求失败'
    )
  }

  return '未知错误'
}