import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import {
  createCategory,
  getCategories,
  type RecipeCategory,
} from '../api/categories'
import {
  createRecipe,
  deleteRecipe,
  getRecipes,
  updateRecipe,
  type Recipe,
  type RecipeCreateParams,
} from '../api/recipes'
import { uploadRecipeImage } from '../api/upload'
import defaultRecipeImage from '../assets/default-recipe-image.jpg'
import { getErrorMessage } from '../utils/error'
import './recipes.css'

const MAX_IMAGE_SIZE = 5 * 1024 * 1024
const ALLOWED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp'])

interface RecipeFormState {
  name: string
  description: string
  price: string
  categoryId: string
  imageUrl: string
  status: 'active' | 'inactive'
}

function emptyForm(categories: RecipeCategory[]): RecipeFormState {
  return {
    name: '',
    description: '',
    price: '',
    categoryId: categories[0] ? String(categories[0].id) : '',
    imageUrl: '',
    status: 'active',
  }
}

function recipeToForm(recipe: Recipe): RecipeFormState {
  return {
    name: recipe.name,
    description: recipe.description || '',
    price: String(recipe.price),
    categoryId: String(recipe.category_id),
    imageUrl: recipe.image_url || '',
    status: recipe.status,
  }
}

function formatPrice(price: number) {
  return `¥${price.toFixed(2)}`
}

function AdminRecipes() {
  const [categories, setCategories] = useState<RecipeCategory[]>([])
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [form, setForm] = useState<RecipeFormState>(() => emptyForm([]))
  const [editingRecipeId, setEditingRecipeId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState('')
  const [creatingCategory, setCreatingCategory] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const navigate = useNavigate()

  const loadManagementData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [categoryResponse, recipeResponse] = await Promise.all([
        getCategories(),
        getRecipes({ page: 1, page_size: 100 }),
      ])
      setCategories(categoryResponse.data)
      setRecipes(recipeResponse.data.items)
      setForm((current) => {
        const hasSelectedCategory = categoryResponse.data.some(
          (category) => String(category.id) === current.categoryId,
        )
        return hasSelectedCategory ? current : emptyForm(categoryResponse.data)
      })
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadManagementData()
  }, [loadManagementData])

  const resetForm = () => {
    setEditingRecipeId(null)
    setForm(emptyForm(categories))
  }

  const updateForm = <Field extends keyof RecipeFormState>(
    field: Field,
    value: RecipeFormState[Field],
  ) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleCreateCategory = async () => {
    const name = newCategoryName.trim()
    if (!name) {
      setError('请输入分类名称')
      return
    }
    if (name.length > 50) {
      setError('分类名称不能超过 50 个字符')
      return
    }

    try {
      setCreatingCategory(true)
      setError(null)
      const response = await createCategory({ name })
      setCategories((current) => [...current, response.data])
      updateForm('categoryId', String(response.data.id))
      setNewCategoryName('')
      setNotice('分类已新增，并已选中该分类')
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setCreatingCategory(false)
    }
  }

  const handleImageUpload = async (file: File | null) => {
    if (!file) {
      return
    }
    if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
      setError('仅支持 JPEG、PNG 和 WebP 图片')
      return
    }
    if (file.size > MAX_IMAGE_SIZE) {
      setError('图片大小不能超过 5 MB')
      return
    }

    try {
      setUploading(true)
      setError(null)
      const response = await uploadRecipeImage(file)
      updateForm('imageUrl', response.data.url)
      setNotice('图片上传成功')
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const categoryId = Number(form.categoryId)
    const price = Number(form.price)
    if (!form.name.trim() || !Number.isInteger(categoryId) || categoryId <= 0) {
      setError('请填写菜谱名称并选择分类')
      return
    }
    if (!Number.isFinite(price) || price < 0) {
      setError('请输入有效价格')
      return
    }

    const payload: RecipeCreateParams = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price,
      category_id: categoryId,
      image_url: form.imageUrl || null,
      status: form.status,
    }

    try {
      setSaving(true)
      setError(null)
      if (editingRecipeId === null) {
        await createRecipe(payload)
        setNotice('菜谱已新增')
      } else {
        await updateRecipe(editingRecipeId, payload)
        setNotice('菜谱已更新')
      }
      resetForm()
      await loadManagementData()
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = (recipe: Recipe) => {
    setEditingRecipeId(recipe.id)
    setForm(recipeToForm(recipe))
    setError(null)
    setNotice(null)
  }

  const handleStatusChange = async (recipe: Recipe) => {
    const nextStatus = recipe.status === 'active' ? 'inactive' : 'active'
    try {
      setError(null)
      await updateRecipe(recipe.id, { status: nextStatus })
      setNotice(nextStatus === 'active' ? '菜谱已上架' : '菜谱已下架')
      await loadManagementData()
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    }
  }

  const handleDelete = async (recipe: Recipe) => {
    if (!window.confirm(`确定删除“${recipe.name}”吗？历史订单存在时将被后端拒绝。`)) {
      return
    }
    try {
      setError(null)
      await deleteRecipe(recipe.id)
      if (editingRecipeId === recipe.id) {
        resetForm()
      }
      setNotice('菜谱已删除')
      await loadManagementData()
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError))
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <main className="recipes-page admin-recipes-page">
      <header className="recipes-header">
        <div>
          <p className="recipes-eyebrow">FYALLSTACK ADMIN</p>
          <h1>菜谱管理</h1>
        </div>
        <nav aria-label="主导航" className="recipes-nav">
          <Link to="/recipes">菜谱</Link>
          <Link aria-current="page" to="/admin/recipes">管理</Link>
          {/* <Link to="/tasks">任务</Link> */}
          <button className="text-action" onClick={logout} type="button">退出</button>
        </nav>
      </header>

      {error ? <div className="admin-notice admin-notice-error" role="alert">{error}</div> : null}
      {notice ? <div className="admin-notice" role="status">{notice}</div> : null}

      <section className="admin-layout">
        <form className="recipe-form" onSubmit={handleSubmit}>
          <div className="recipe-form-heading">
            <h2>{editingRecipeId === null ? '新增菜谱' : '编辑菜谱'}</h2>
            {editingRecipeId !== null ? (
              <button className="text-action" onClick={resetForm} type="button">取消编辑</button>
            ) : null}
          </div>

          <label>
            菜谱名称
            <input
              maxLength={100}
              onChange={(event) => updateForm('name', event.target.value)}
              required
              value={form.name}
            />
          </label>
          <label>
            菜谱描述
            <textarea
              maxLength={5000}
              onChange={(event) => updateForm('description', event.target.value)}
              rows={4}
              value={form.description}
            />
          </label>
          <div className="recipe-form-row">
            <label>
              价格
              <input
                min="0"
                onChange={(event) => updateForm('price', event.target.value)}
                required
                step="0.01"
                type="number"
                value={form.price}
              />
            </label>
            <label>
              分类
              <select
                disabled={categories.length === 0}
                onChange={(event) => updateForm('categoryId', event.target.value)}
                required
                value={form.categoryId}
              >
                {categories.length === 0 ? <option value="">暂无分类</option> : null}
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>{category.name}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="category-create-row">
            <input
              aria-label="新分类名称"
              disabled={creatingCategory}
              maxLength={50}
              onChange={(event) => setNewCategoryName(event.target.value)}
              placeholder="输入新分类名称"
              value={newCategoryName}
            />
            <button
              disabled={creatingCategory}
              onClick={() => void handleCreateCategory()}
              type="button"
            >
              {creatingCategory ? '正在新增' : '新增分类'}
            </button>
          </div>
          <label>
            状态
            <select
              onChange={(event) => updateForm('status', event.target.value as RecipeFormState['status'])}
              value={form.status}
            >
              <option value="active">上架</option>
              <option value="inactive">下架</option>
            </select>
          </label>
          <label>
            菜谱图片
            <input
              accept="image/jpeg,image/png,image/webp"
              disabled={uploading}
              onChange={(event) => void handleImageUpload(event.target.files?.[0] || null)}
              type="file"
            />
          </label>
          <img
            alt="菜谱图片预览"
            className="recipe-form-preview"
            onError={(event) => {
              event.currentTarget.onerror = null
              event.currentTarget.src = defaultRecipeImage
            }}
            src={form.imageUrl || defaultRecipeImage}
          />
          <button
            className="admin-primary-action"
            disabled={saving || uploading || categories.length === 0}
            type="submit"
          >
            {uploading ? '正在上传图片' : saving ? '正在保存' : editingRecipeId === null ? '保存菜谱' : '更新菜谱'}
          </button>
        </form>

        <section aria-label="管理员菜谱列表" className="admin-recipe-list">
          <div className="admin-list-heading">
            <h2>全部菜谱</h2>
            <span>{recipes.length} 道</span>
          </div>
          {loading ? <div className="admin-list-state" role="status">正在加载管理数据</div> : null}
          {!loading && recipes.length === 0 ? <div className="admin-list-state">暂无菜谱</div> : null}
          {!loading && recipes.length > 0 ? (
            <div className="admin-table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>菜谱</th>
                    <th>分类</th>
                    <th>价格</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {recipes.map((recipe) => (
                    <tr key={recipe.id}>
                      <td>
                        <div className="admin-recipe-name">
                          <img
                            alt=""
                            onError={(event) => {
                              event.currentTarget.onerror = null
                              event.currentTarget.src = defaultRecipeImage
                            }}
                            src={recipe.image_url || defaultRecipeImage}
                          />
                          <span>{recipe.name}</span>
                        </div>
                      </td>
                      <td>{recipe.category_name}</td>
                      <td>{formatPrice(recipe.price)}</td>
                      <td>
                        <span className={`recipe-status recipe-status-${recipe.status}`}>
                          {recipe.status === 'active' ? '上架' : '下架'}
                        </span>
                      </td>
                      <td>
                        <div className="admin-row-actions">
                          <button onClick={() => handleEdit(recipe)} type="button">编辑</button>
                          <button onClick={() => void handleStatusChange(recipe)} type="button">
                            {recipe.status === 'active' ? '下架' : '上架'}
                          </button>
                          <button className="danger-action" onClick={() => void handleDelete(recipe)} type="button">删除</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </section>
    </main>
  )
}

export default AdminRecipes
