import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  getAdminOrder,
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

function AdminOrderDetail() {
  const { orderId } = useParams()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const navigate = useNavigate()

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
      const response = await getAdminOrder(id)
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

  const handleStatusChange = async (nextStatus: OrderStatus) => {
    if (!order || order.status === nextStatus) {
      return
    }
    try {
      setUpdating(true)
      setError(null)
      setNotice(null)
      const response = await updateAdminOrderStatus(order.id, nextStatus)
      setOrder(response.data)
      setNotice(`订单状态已更新为${statusLabels[nextStatus]}`)
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setUpdating(false)
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
          <h1>订单详情</h1>
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
      {loading ? <div className="admin-list-state" role="status">正在加载订单</div> : null}

      {!loading && order ? (
        <section aria-label="管理员订单详情" className="admin-order-detail">
          <div className="admin-detail-heading">
            <div>
              <Link to="/admin/orders">返回订单列表</Link>
              <h2>订单 #{order.id}</h2>
            </div>
            <span className={`order-status order-status-${order.status}`}>
              {statusLabels[order.status]}
            </span>
          </div>
          <dl className="admin-order-meta">
            <div><dt>用户</dt><dd>用户 #{order.user_id}</dd></div>
            <div><dt>创建时间</dt><dd>{formatDate(order.created_at)}</dd></div>
            <div><dt>更新时间</dt><dd>{formatDate(order.updated_at)}</dd></div>
            <div><dt>订单总额</dt><dd className="admin-order-total">{formatAmount(order.total_amount)}</dd></div>
          </dl>
          <div className="admin-detail-items">
            <h3>菜品明细</h3>
            <div className="admin-table-scroll">
              <table>
                <thead>
                  <tr><th>菜品</th><th>下单价格</th><th>数量</th><th>小计</th></tr>
                </thead>
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
          <div className="admin-detail-actions">
            <label>
              修改状态
              <select
                disabled={updating || order.status !== 'pending'}
                onChange={(event) => void handleStatusChange(event.target.value as OrderStatus)}
                value={order.status}
              >
                <option value="pending">待处理</option>
                <option value="completed">已完成</option>
                <option value="cancelled">已取消</option>
              </select>
            </label>
            {order.status !== 'pending' ? <span>终态订单不可再次修改</span> : null}
          </div>
        </section>
      ) : null}
    </main>
  )
}

export default AdminOrderDetail
