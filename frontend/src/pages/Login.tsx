import { useState, type SubmitEvent } from 'react'

import { Link, useNavigate } from 'react-router-dom'
import './index.css'
import { login } from '../api/auth'

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!username.trim() || !password) {
      alert('请输入用户名和密码')
      return
    }

    try {
      setLoading(true)

      const response = await login({
        username,
        password,
      })

      localStorage.setItem(
        'access_token',
        response.data.access_token,
      )

      navigate('/tasks')
    } catch (error: any) {
      console.error(error.response?.data?.message)
      alert(error.response?.data?.detail || error.response?.data?.message || '登录失败1')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>登录页3</h1>

        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="用户名"
        />

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="密码"
        />

        <button type="submit">
          {loading ? '登录中...' : '登录'}
        </button>

        <p>
          没有账号？
          <Link to="/register">去注册</Link>
        </p>
      </form>
    </div>
  )
}

export default Login
