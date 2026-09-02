import { useState, type SubmitEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './index.css'
import { register } from '../api/auth'

function Register() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const navigate = useNavigate()

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!username.trim() || !password) {
      alert('请输入用户名和密码')
      return
    }
    if (password !== confirmPassword) {
      alert('两次密码不一致')
      return
    }

    console.log({
      username,
      password,
    })
    try {
      setLoading(true)

      await register({
        username,
        password,
      })

      alert('注册成功')
      navigate('/login')
    } catch (error: any) {
      alert(error.response?.data?.detail || '注册失败')
    } finally {
      setLoading(false)
    }

  }

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>注册</h1>

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

        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="确认密码"
        />

        <button type="submit">
        {loading ? '注册中...' : '注册'}
        </button>

        <p>
          已有账号？
          <Link to="/login">去登录</Link>
        </p>
      </form>
    </div>
  )
}

export default Register
