import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { getCategories, type RecipeCategory } from '../api/categories'
import {
  getRecipes,
  type Recipe,
  type RecipeListResponse,
} from '../api/recipes'
import defaultRecipeImage from '../assets/default-recipe-image.jpg'
import { getCurrentUserRole } from '../utils/auth'
import { getErrorMessage } from '../utils/error'
import './recipes.css'

const PAGE_SIZE = 8

function formatPrice(price: number) {
  return `¥${price.toFixed(2)}`
}

function Recipes() {
  const [categories, setCategories] = useState<RecipeCategory[]>([])
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const isAdmin = getCurrentUserRole() === 'admin'

  const loadRecipes = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getRecipes({
        page,
        page_size: PAGE_SIZE,
        ...(selectedCategoryId ? { category_id: selectedCategoryId } : {}),
      })
      const payload: RecipeListResponse = response.data
      setRecipes(payload.items)
      setTotal(payload.total)
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
      setRecipes([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [page, selectedCategoryId])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadRecipes()
  }, [loadRecipes])

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await getCategories()
        setCategories(response.data)
      } catch (requestError: unknown) {
        setError(getErrorMessage(requestError))
      }
    }

    void loadCategories()
  }, [])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const selectCategory = (categoryId: number | null) => {
    setSelectedCategoryId(categoryId)
    setPage(1)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <main className="recipes-page">
      <header className="recipes-header">
        <div>
          <p className="recipes-eyebrow">FYALLSTACK</p>
          <h1>菜谱</h1>
        </div>
        <nav aria-label="主导航" className="recipes-nav">
          <Link aria-current="page" to="/recipes">菜谱</Link>
          <Link to="/orders">我的订单</Link>
          {isAdmin ? <Link to="/admin/recipes">管理</Link> : null}
          {isAdmin ? <Link to="/admin/orders">订单</Link> : null}
          {/* <Link to="/tasks">任务</Link> */}
          <button className="text-action" onClick={logout} type="button">退出</button>
        </nav>
      </header>

      <section aria-label="菜谱分类" className="category-tabs">
        <button
          aria-pressed={selectedCategoryId === null}
          className={selectedCategoryId === null ? 'is-selected' : ''}
          onClick={() => selectCategory(null)}
          type="button"
        >
          全部
        </button>
        {categories.map((category) => (
          <button
            aria-pressed={selectedCategoryId === category.id}
            className={selectedCategoryId === category.id ? 'is-selected' : ''}
            key={category.id}
            onClick={() => selectCategory(category.id)}
            type="button"
          >
            {category.name}
          </button>
        ))}
      </section>

      {loading ? <div className="recipe-state" role="status">正在加载菜谱</div> : null}

      {!loading && error ? (
        <section className="recipe-state recipe-state-error" role="alert">
          <p>{error}</p>
          <button onClick={() => void loadRecipes()} type="button">重试</button>
        </section>
      ) : null}

      {!loading && !error && recipes.length === 0 ? (
        <div className="recipe-state">当前筛选条件下没有菜谱</div>
      ) : null}

      {!loading && !error && recipes.length > 0 ? (
        <section aria-label="菜谱列表" className="recipe-grid">
          {recipes.map((recipe) => (
            <article className="recipe-card" key={recipe.id}>
              <Link
                aria-label={`查看${recipe.name}详情`}
                className="recipe-image-link"
                to={`/recipes/${recipe.id}`}
              >
                <img
                  alt={recipe.name}
                  className="recipe-image"
                  onError={(event) => {
                    event.currentTarget.onerror = null
                    event.currentTarget.src = defaultRecipeImage
                  }}
                  src={recipe.image_url || defaultRecipeImage}
                />
              </Link>
              <div className="recipe-card-content">
                <p className="recipe-category">{recipe.category_name}</p>
                <h2><Link to={`/recipes/${recipe.id}`}>{recipe.name}</Link></h2>
                <p className="recipe-description">{recipe.description || '暂无菜谱描述'}</p>
                <div className="recipe-card-footer">
                  <strong>{formatPrice(recipe.price)}</strong>
                  <Link className="recipe-detail-link" to={`/recipes/${recipe.id}`}>查看详情</Link>
                </div>
              </div>
            </article>
          ))}
        </section>
      ) : null}

      {!loading && !error && total > 0 ? (
        <nav aria-label="菜谱分页" className="recipe-pagination">
          <button disabled={page === 1} onClick={() => setPage(page - 1)} type="button">上一页</button>
          <span>第 {page} / {totalPages} 页，共 {total} 道</span>
          <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} type="button">下一页</button>
        </nav>
      ) : null}
    </main>
  )
}

export default Recipes
