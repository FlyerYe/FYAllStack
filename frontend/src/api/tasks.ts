import request from '../utils/request'

export interface Task {
  id: number
  title: string
  description: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface CreateTaskParams {
  title: string
  description?: string
}

export interface UpdateTaskParams {
  title?: string
  description?: string
  status?: string
}

export const getTasks = () => {
  return request.get<Task[]>('/tasks')
}

export const createTask = (data: CreateTaskParams) => {
  return request.post<Task>('/tasks', data)
}

export const updateTask = (
  id: number,
  data: UpdateTaskParams,
) => {
  return request.put<Task>(`/tasks/${id}`, data)
}

export const deleteTask = (id: number) => {
  return request.delete(`/tasks/${id}`)
}