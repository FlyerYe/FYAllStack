import request from '../utils/request'

export type OrderStatus = 'pending' | 'completed' | 'cancelled'

export interface OrderItem {
  id: number
  recipe_id: number
  recipe_name: string
  image_url: string | null
  quantity: number
  price: string
  subtotal: string
}

export interface Order {
  id: number
  user_id: number
  status: OrderStatus
  total_amount: string
  created_at: string | null
  updated_at: string | null
  items: OrderItem[]
}

export interface CreateOrderItemParams {
  recipe_id: number
  quantity: number
}

export interface CreateOrderParams {
  items: CreateOrderItemParams[]
}

export const createOrder = (data: CreateOrderParams) =>
  request.post<Order>('/orders', data)

export const getOrders = () => request.get<Order[]>('/orders')

export const getOrder = (id: number) => request.get<Order>(`/orders/${id}`)

export const cancelOrder = (id: number) => request.post(`/orders/${id}/cancel`)

export const getAdminOrders = (status?: OrderStatus) =>
  request.get<Order[]>('/admin/orders', {
    params: status ? { status } : undefined,
  })

export const getAdminOrder = (id: number) =>
  request.get<Order>(`/admin/orders/${id}`)

export const updateAdminOrderStatus = (id: number, status: OrderStatus) =>
  request.put<Order>(`/admin/orders/${id}/status`, { status })
