import request from '../utils/request'

export interface ImageUploadResponse {
  url: string
}

export const uploadRecipeImage = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<ImageUploadResponse>('/upload/image', formData)
}
