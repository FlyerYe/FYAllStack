import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { getRecipe, type Recipe } from '../api/recipes'
import { createOrder } from '../api/orders'
import defaultRecipeImage from '../assets/default-recipe-image.jpg'
import { getCurrentUserRole } from '../utils/auth'
import { getErrorMessage } from '../utils/error'
import './recipes.css'

function formatPrice(price: number) {
  return `¥${price.toFixed(2)}`
}

function RecipeDetail() {
  const { recipeId } = useParams()
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [loading, setLoading] = useState(true)
  const [ordering, setOrdering] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const isAdmin = getCurrentUserRole() === 'admin'

  const loadRecipe = useCallback(async () => {
    const id = Number(recipeId)
    if (!Number.isInteger(id) || id <= 0) {
      setError('菜谱不存在')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await getRecipe(id)
      setRecipe(response.data)
    } catch (requestError: unknown) {
      setRecipe(null)
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [recipeId])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadRecipe()
  }, [loadRecipe])

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const handleOrder = async () => {
    if (!recipe) {
      return
    }
    try {
      setOrdering(true)
      setError(null)
      const response = await createOrder({
        items: [{ recipe_id: recipe.id, quantity }],
      })
      navigate(`/orders/${response.data.id}`)
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setOrdering(false)
    }
  }

  return (
    <main className="recipes-page">
      <header className="recipes-header">
        <div>
          <p className="recipes-eyebrow">FYALLSTACK</p>
          <h1>菜谱详情</h1>
        </div>
        <nav aria-label="主导航" className="recipes-nav">
          <Link to="/recipes">菜谱</Link>
          <Link to="/orders">我的订单</Link>
          {isAdmin ? <Link to="/admin/recipes">管理</Link> : null}
          {isAdmin ? <Link to="/admin/orders">订单</Link> : null}
          {/* <Link to="/tasks">任务</Link> */}
          <button className="text-action" onClick={logout} type="button">退出</button>
        </nav>
      </header>

      {loading ? <div className="recipe-state" role="status">正在加载菜谱详情</div> : null}

      {!loading && error ? (
        <section className="recipe-state recipe-state-error" role="alert">
          <p>{error}</p>
          <div className="recipe-state-actions">
            <button onClick={() => void loadRecipe()} type="button">重试</button>
            <Link to="/recipes">返回菜谱</Link>
          </div>
        </section>
      ) : null}

      {!loading && !error && recipe ? (
        <article className="recipe-detail">
          <img
            alt={recipe.name}
            className="recipe-detail-image"
            onError={(event) => {
              event.currentTarget.onerror = null
              event.currentTarget.src = defaultRecipeImage
            }}
            src={recipe.image_url || defaultRecipeImage}
          />
          <div className="recipe-detail-content">
            <p className="recipe-category">{recipe.category_name}</p>
            <h2>{recipe.name}</h2>
            <p className="recipe-detail-description">{recipe.description || '暂无菜谱描述'}</p>
            <strong className="recipe-price">{formatPrice(recipe.price)}</strong>
            <div className="quantity-control">
              <span>点菜数量</span>
              <div>
                <button aria-label="减少数量" disabled={quantity === 1} onClick={() => setQuantity(quantity - 1)} type="button">-</button>
                <output>{quantity}</output>
                <button aria-label="增加数量" onClick={() => setQuantity(quantity + 1)} type="button">+</button>
              </div>
            </div>
            <button className="order-button" disabled={ordering} onClick={() => void handleOrder()} type="button">
              {ordering ? '正在创建订单' : '点菜'}
            </button>
          </div>
        </article>
      ) : null}
    </main>
  )
}

export default RecipeDetail
