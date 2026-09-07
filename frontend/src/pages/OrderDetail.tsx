import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { cancelOrder, getOrder, type Order, type OrderStatus } from '../api/orders'
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

function OrderDetail() {
  const { orderId } = useParams()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const navigate = useNavigate()
  const isAdmin = getCurrentUserRole() === 'admin'

  const loadOrder = useCallback(async () => {
    const id = Number(orderId)
    if (!Number.isInteger(id) || id <= 0) {
      setError('订单编号无效')
      setLoading(false)
      return
    }
    try {
      setLoading(true)
      setError(null)
      const response = await getOrder(id)
      setOrder(response.data)
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
      setOrder(null)
    } finally {
      setLoading(false)
    }
  }, [orderId])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadOrder()
  }, [loadOrder])

  const handleCancel = async () => {
    if (!order || order.status !== 'pending' || !window.confirm(`确定取消订单 #${order.id} 吗？`)) {
      return
    }
    try {
      setCancelling(true)
      setError(null)
      setNotice(null)
      await cancelOrder(order.id)
      setNotice('订单已取消')
      await loadOrder()
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setCancelling(false)
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
          <h1>订单详情</h1>
        </div>
        <nav aria-label="主导航" className="recipes-nav">
          <Link to="/recipes">菜谱</Link>
          <Link aria-current="page" to="/orders">我的订单</Link>
          {isAdmin ? <Link to="/admin/orders">订单管理</Link> : null}
          <button className="text-action" onClick={logout} type="button">退出</button>
        </nav>
      </header>

      {error ? <div className="admin-notice admin-notice-error" role="alert">{error}</div> : null}
      {notice ? <div className="admin-notice" role="status">{notice}</div> : null}
      {loading ? <div className="admin-list-state" role="status">正在加载订单</div> : null}
      {!loading && order ? (
        <section aria-label="我的订单详情" className="user-order-detail">
          <div className="admin-detail-heading">
            <div>
              <Link to="/orders">返回我的订单</Link>
              <h2>订单 #{order.id}</h2>
            </div>
            <span className={`order-status order-status-${order.status}`}>
              {statusLabels[order.status]}
            </span>
          </div>
          <dl className="admin-order-meta">
            <div><dt>创建时间</dt><dd>{formatDate(order.created_at)}</dd></div>
            <div><dt>更新时间</dt><dd>{formatDate(order.updated_at)}</dd></div>
            <div><dt>订单总额</dt><dd className="admin-order-total">{formatAmount(order.total_amount)}</dd></div>
          </dl>
          <div className="admin-detail-items">
            <h3>菜品明细</h3>
            <div className="admin-table-scroll">
              <table>
                <thead><tr><th>菜品</th><th>下单价格</th><th>数量</th><th>小计</th></tr></thead>
                <tbody>
                  {order.items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.recipe_name}</td>
                      <td>{formatAmount(item.price)}</td>
                      <td>{item.quantity}</td>
                      <td>{formatAmount(item.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {order.status === 'pending' ? (
            <div className="user-order-actions">
              <button disabled={cancelling} onClick={() => void handleCancel()} type="button">
                {cancelling ? '正在取消' : '取消订单'}
              </button>
            </div>
          ) : null}
        </section>
      ) : null}
    </main>
  )
}

export default OrderDetail
