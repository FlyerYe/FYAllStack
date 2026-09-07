import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import {
  getAdminOrders,
  updateAdminOrderStatus,
  type Order,
  type OrderStatus,
} from '../api/orders'
import { getErrorMessage } from '../utils/error'
import './orders.css'

const statusLabels: Record<OrderStatus, string> = {
  pending: '待处理',
  completed: '已完成',
  cancelled: '已取消',
}

function formatAmount(amount: string) {
  return `¥${Number(amount).toFixed(2)}`
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
}

function AdminOrders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [statusFilter, setStatusFilter] = useState<OrderStatus | ''>('')
  const [loading, setLoading] = useState(true)
  const [updatingOrderId, setUpdatingOrderId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const navigate = useNavigate()

  const loadOrders = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getAdminOrders(statusFilter || undefined)
      setOrders(response.data)
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
      setOrders([])
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadOrders()
  }, [loadOrders])

  const handleStatusChange = async (order: Order, nextStatus: OrderStatus) => {
    if (order.status === nextStatus) {
      return
    }
    try {
      setUpdatingOrderId(order.id)
      setError(null)
      setNotice(null)
      await updateAdminOrderStatus(order.id, nextStatus)
      setNotice(`订单 #${order.id} 状态已更新为${statusLabels[nextStatus]}`)
      await loadOrders()
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setUpdatingOrderId(null)
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <main className="recipes-page admin-orders-page">
      <header className="recipes-header">
        <div>
          <p className="recipes-eyebrow">FYALLSTACK ADMIN</p>
          <h1>订单管理</h1>
        </div>
        <nav aria-label="主导航" className="recipes-nav">
          <Link to="/recipes">菜谱</Link>
          <Link to="/admin/recipes">菜谱管理</Link>
          <Link aria-current="page" to="/admin/orders">订单</Link>
          {/* <Link to="/tasks">任务</Link> */}
          <button className="text-action" onClick={logout} type="button">退出</button>
        </nav>
      </header>

      {error ? <div className="admin-notice admin-notice-error" role="alert">{error}</div> : null}
      {notice ? <div className="admin-notice" role="status">{notice}</div> : null}

      <section aria-label="订单筛选和列表" className="admin-orders-list">
        <div className="admin-list-heading admin-orders-toolbar">
          <div>
            <h2>全部订单</h2>
            <span>{orders.length} 笔</span>
          </div>
          <label>
            状态
            <select
              onChange={(event) => setStatusFilter(event.target.value as OrderStatus | '')}
              value={statusFilter}
            >
              <option value="">全部</option>
              <option value="pending">待处理</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
            </select>
          </label>
        </div>

        {loading ? <div className="admin-list-state" role="status">正在加载订单</div> : null}
        {!loading && !error && orders.length === 0 ? (
          <div className="admin-list-state">当前筛选条件下没有订单</div>
        ) : null}
        {!loading && orders.length > 0 ? (
          <div className="admin-table-scroll">
            <table>
              <thead>
                <tr>
                  <th>订单</th>
                  <th>用户</th>
                  <th>明细</th>
                  <th>总额</th>
                  <th>创建时间</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td><Link to={`/admin/orders/${order.id}`}>#{order.id}</Link></td>
                    <td>用户 #{order.user_id}</td>
                    <td>
                      <ul className="admin-order-items">
                        {order.items.map((item) => (
                          <li key={item.id}>
                            {item.recipe_name} × {item.quantity}，{formatAmount(item.price)}
                          </li>
                        ))}
                      </ul>
                    </td>
                    <td className="admin-order-total">{formatAmount(order.total_amount)}</td>
                    <td>{formatDate(order.created_at)}</td>
                    <td>
                      <select
                        aria-label={`修改订单 ${order.id} 状态`}
                        disabled={updatingOrderId === order.id || order.status !== 'pending'}
                        onChange={(event) => void handleStatusChange(order, event.target.value as OrderStatus)}
                        value={order.status}
                      >
                        <option value="pending">待处理</option>
                        <option value="completed">已完成</option>
                        <option value="cancelled">已取消</option>
                      </select>
                      <span className={`order-status order-status-${order.status}`}>
                        {statusLabels[order.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </main>
  )
}

export default AdminOrders
