import request from '../utils/request'

export interface RegisterParams {
  username: string
  password: string
}

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export const register = (data: RegisterParams) => {
  return request.post('/auth/register', data)
}

export const login = (data: LoginParams) => {
  return request.post<LoginResponse>('/auth/login', data)
}