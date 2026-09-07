import request from '../utils/request'

export interface Recipe {
  id: number
  name: string
  description: string | null
  price: number
  image_url: string | null
  category_id: number
  category_name: string
  status: 'active' | 'inactive'
  created_at: string | null
  updated_at: string | null
}

export interface RecipeListResponse {
  items: Recipe[]
  page: number
  page_size: number
  total: number
}

export interface RecipeListParams {
  page: number
  page_size: number
  category_id?: number
  status?: Recipe['status']
}

export interface RecipeCreateParams {
  name: string
  description: string | null
  price: number
  category_id: number
  image_url: string | null
  status: Recipe['status']
}

export type RecipeUpdateParams = Partial<RecipeCreateParams>

export const getRecipes = (params: RecipeListParams) =>
  request.get<RecipeListResponse>('/recipes', { params })

export const getRecipe = (id: number) => request.get<Recipe>(`/recipes/${id}`)

export const createRecipe = (data: RecipeCreateParams) =>
  request.post<Recipe>('/recipes', data)

export const updateRecipe = (id: number, data: RecipeUpdateParams) =>
  request.put<Recipe>(`/recipes/${id}`, data)

export const deleteRecipe = (id: number) => request.delete(`/recipes/${id}`)
