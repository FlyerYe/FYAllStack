import request from '../utils/request'

export interface RecipeCategory {
  id: number
  name: string
  created_at: string | null
}

export const getCategories = () => request.get<RecipeCategory[]>('/categories')

export interface CategoryCreateParams {
  name: string
}

export const createCategory = (data: CategoryCreateParams) =>
  request.post<RecipeCategory>('/categories', data)
