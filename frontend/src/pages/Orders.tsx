import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { cancelOrder, getOrders, type Order, type OrderStatus } from '../api/orders'
import { getCurrentUserRole } from '../utils/auth'
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

function Orders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [cancellingOrderId, setCancellingOrderId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const navigate = useNavigate()
  const isAdmin = getCurrentUserRole() === 'admin'

  const loadOrders = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getOrders()
      setOrders(response.data)
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
      setOrders([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadOrders()
  }, [loadOrders])

  const handleCancel = async (order: Order) => {
    if (!window.confirm(`确定取消订单 #${order.id} 吗？`)) {
      return
    }
    try {
      setCancellingOrderId(order.id)
      setError(null)
      setNotice(null)
      await cancelOrder(order.id)
      setNotice(`订单 #${order.id} 已取消`)
      await loadOrders()
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setCancellingOrderId(null)
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <main className="recipes-page user-orders-page">
      <header className="recipes-header">
        <div>
          <p className="recipes-eyebrow">FYALLSTACK</p>
          <h1>我的订单</h1>
        </div>
        <nav aria-label="主导航" className="recipes-nav">
          <Link to="/recipes">菜谱</Link>
          <Link aria-current="page" to="/orders">我的订单</Link>
          {isAdmin ? <Link to="/admin/recipes">管理</Link> : null}
          {isAdmin ? <Link to="/admin/orders">订单管理</Link> : null}
          <button className="text-action" onClick={logout} type="button">退出</button>
        </nav>
      </header>

      {error ? <div className="admin-notice admin-notice-error" role="alert">{error}</div> : null}
      {notice ? <div className="admin-notice" role="status">{notice}</div> : null}
      {loading ? <div className="admin-list-state" role="status">正在加载订单</div> : null}
      {!loading && !error && orders.length === 0 ? (
        <div className="admin-list-state">还没有订单，去菜谱页面点一道菜吧</div>
      ) : null}
      {!loading && orders.length > 0 ? (
        <section aria-label="我的订单列表" className="user-orders-list">
          {orders.map((order) => (
            <article className="user-order-row" key={order.id}>
              <div className="user-order-heading">
                <Link to={`/orders/${order.id}`}>订单 #{order.id}</Link>
                <span className={`order-status order-status-${order.status}`}>
                  {statusLabels[order.status]}
                </span>
              </div>
              <p className="user-order-date">{formatDate(order.created_at)}</p>
              <ul className="user-order-items">
                {order.items.map((item) => (
                  <li key={item.id}>
                    {item.recipe_name} × {item.quantity}，{formatAmount(item.price)}
                  </li>
                ))}
              </ul>
              <div className="user-order-footer">
                <strong>{formatAmount(order.total_amount)}</strong>
                {order.status === 'pending' ? (
                  <button
                    disabled={cancellingOrderId === order.id}
                    onClick={() => void handleCancel(order)}
                    type="button"
                  >
                    {cancellingOrderId === order.id ? '正在取消' : '取消订单'}
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </section>
      ) : null}
    </main>
  )
}

export default Orders
