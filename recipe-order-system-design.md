# FYAllStack 菜谱与点餐系统方案设计

## 1. 项目背景

在现有 FYAllStack 全栈项目基础上，新增“菜谱与点餐系统”。

现有技术栈：

- 前端：React + TypeScript + Vite
- 后端：Python + FastAPI
- 数据库：PostgreSQL
- 缓存：Redis
- 鉴权：JWT
- 文件存储：阿里云 OSS
- Web：Nginx
- 部署：Docker Compose + 阿里云 ECS
- CI/CD：GitHub Actions

现有系统已经具备：

- 用户注册
- 用户登录
- JWT 鉴权
- Task CRUD
- Redis Cache Aside
- Docker 部署
- ECS + Nginx + HTTPS
- GitHub Actions 自动部署

本次新增菜谱系统，并扩展用户角色、菜谱管理、图片上传、分类浏览和点餐功能。

---

# 2. 业务目标

系统包含两个角色：

```text
管理员 Admin
    │
    ├── 管理菜谱
    ├── 管理分类
    ├── 上传菜谱图片
    └── 查看/管理订单

普通用户 User
    │
    ├── 浏览菜谱
    ├── 分类筛选
    ├── 分页查看
    ├── 点菜
    └── 查看自己的订单
```

核心业务链路：

```text
登录
  ↓
JWT 鉴权
  ↓
识别用户角色
  ├───────────────┐
  ↓               ↓
Admin             User
  ↓               ↓
菜谱管理           浏览菜谱
分类管理           分类筛选
订单管理           点菜
```

---

# 3. 角色设计

## 3.1 Admin

管理员可以：

- 新增菜谱
- 修改菜谱
- 删除菜谱
- 上架/下架菜谱
- 上传菜谱图片
- 管理菜谱分类
- 查看订单
- 修改订单状态

管理员不能通过前端权限绕过后端权限控制。

所有管理员 API 必须在后端进行角色校验。

---

## 3.2 User

普通用户可以：

- 浏览菜谱
- 查看菜谱详情
- 按分类筛选
- 分页浏览
- 创建订单
- 查看自己的订单
- 取消自己的订单

普通用户不能：

- 创建菜谱
- 修改菜谱
- 删除菜谱
- 修改分类
- 修改其他用户订单

---

# 4. 权限设计原则

采用：

```text
前端权限控制 + 后端权限控制
```

前端：

```text
根据 role 控制菜单、按钮和路由
```

后端：

```text
JWT
 ↓
user_id
 ↓
role
 ↓
权限判断
```

后端是真正的安全边界。

例如：

```http
DELETE /api/recipes/10
```

后端必须检查：

```text
当前用户是否登录？
    ↓
是否存在？
    ↓
role 是否为 admin？
    ↓
是 → 执行删除
否 → 403 Forbidden
```

---

# 5. 用户角色设计

现有 `users` 表增加：

```sql
role VARCHAR(20) NOT NULL DEFAULT 'user'
```

角色值：

```text
admin
user
```

示例：

```text
id | username | role
---|----------|------
1  | admin    | admin
2  | user01   | user
```

---

# 6. JWT 设计

JWT Payload 增加角色信息：

```json
{
  "sub": "1",
  "role": "admin",
  "exp": 1788500000
}
```

字段：

| 字段 | 含义 |
|---|---|
| sub | 用户 ID |
| role | 用户角色 |
| exp | Token 过期时间 |

后端解析 JWT 后得到：

```python
{
    "user_id": 1,
    "role": "admin"
}
```

---

# 7. 后端权限模块

建议增加：

```text
app/core/security.py
```

提供：

```python
get_current_user()
require_admin()
```

逻辑：

```text
get_current_user
    ↓
验证 JWT
    ↓
获取 user_id
    ↓
获取 role
```

管理员接口：

```python
current_user = require_admin(...)
```

普通用户接口只需要：

```python
current_user = get_current_user(...)
```

---

# 8. 数据库设计

整体关系：

```text
users
  │
  │ 1:N
  ↓
orders
  │
  │ 1:N
  ↓
order_items
  │
  │ N:1
  ↓
recipes
  │
  │ N:1
  ↓
recipe_categories
```

---

## 8.1 users

现有表增加：

```sql
role VARCHAR(20) NOT NULL DEFAULT 'user'
```

完整结构：

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8.2 recipe_categories

```sql
CREATE TABLE recipe_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

示例：

```text
1 中餐
2 西餐
3 日料
4 甜品
5 饮品
```

分类由管理员管理，普通用户只能查询。

---

## 8.3 recipes

```sql
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL DEFAULT 0,
    image_url VARCHAR(500),
    category_id INTEGER NOT NULL REFERENCES recipe_categories(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

字段含义：

| 字段 | 含义 |
|---|---|
| name | 菜谱名称 |
| description | 菜谱描述 |
| price | 当前售价 |
| image_url | OSS 图片地址 |
| category_id | 分类 |
| status | 上架/下架 |

状态：

```text
active
inactive
```

不建议使用物理删除代替下架。

---

## 8.4 orders

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

订单状态：

```text
pending
confirmed
completed
cancelled
```

第一版可以先实现：

```text
pending
completed
cancelled
```

---

## 8.5 order_items

```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    recipe_id INTEGER NOT NULL REFERENCES recipes(id),
    quantity INTEGER NOT NULL,
    price NUMERIC(10,2) NOT NULL
);
```

`price` 必须保存下单时的价格快照。

例如：

```text
今天：

宫保鸡丁 = 28

用户下单：

order_items.price = 28
```

即使以后：

```text
recipes.price = 35
```

历史订单仍然保持：

```text
28
```

---

# 9. OSS 图片方案

使用已有阿里云 OSS。

自定义域名：

```text
https://static.myfeiniao.cn
```

图片目录：

```text
recipes/
```

最终图片：

```text
https://static.myfeiniao.cn/recipes/xxxxxxxx.jpg
```

数据库只保存：

```text
image_url
```

不保存图片二进制。

---

# 10. 图片上传规则

图片可选。

上传：

```text
图片
 ↓
FastAPI
 ↓
OSS
 ↓
image_url
```

不上传：

```text
image_url = NULL
```

前端：

```tsx
<img
  src={recipe.image_url || defaultRecipeImage}
  alt={recipe.name}
/>
```

默认图片由前端提供。

---

# 11. 图片上传接口

接口：

```http
POST /api/upload/image
```

请求：

```text
multipart/form-data
```

字段：

```text
file
```

返回：

```json
{
  "url": "https://static.myfeiniao.cn/recipes/xxxx.jpg"
}
```

后端：

```text
UploadFile
 ↓
校验 MIME Type
 ↓
检查是否为 image/*
 ↓
生成 UUID 文件名
 ↓
上传 OSS
 ↓
返回 URL
```

文件名不要直接使用用户原始文件名。

建议：

```text
recipes/{uuid}.{ext}
```

例如：

```text
recipes/c53c811f880411ebb6edd017c2d2eca2.jpg
```

---

# 12. OSS 安全设计

OSS AccessKey 不允许出现在前端。

只允许：

```text
FastAPI
```

读取 OSS AccessKey。

配置放到：

```text
.env
```

例如：

```env
OSS_ACCESS_KEY_ID=xxx
OSS_ACCESS_KEY_SECRET=xxx
OSS_REGION=xxx
OSS_BUCKET=xxx
OSS_ENDPOINT=xxx
OSS_DOMAIN=https://static.myfeiniao.cn
```

`.env` 不提交 Git。

---

# 13. 菜谱 API

## 13.1 查询菜谱

```http
GET /api/recipes
```

支持参数：

```text
page
page_size
category_id
status
```

例如：

```http
GET /api/recipes?page=1&page_size=10
```

分类：

```http
GET /api/recipes?page=1&page_size=10&category_id=2
```

返回：

```json
{
  "items": [
    {
      "id": 1,
      "name": "宫保鸡丁",
      "description": "经典川菜",
      "price": 28,
      "image_url": "https://static.myfeiniao.cn/recipes/a.jpg",
      "category_id": 1,
      "category_name": "中餐",
      "status": "active"
    }
  ],
  "page": 1,
  "page_size": 10,
  "total": 35
}
```

普通用户只能查询：

```text
status = active
```

管理员可以查看全部状态。

---

## 13.2 菜谱详情

```http
GET /api/recipes/{id}
```

---

## 13.3 创建菜谱

```http
POST /api/recipes
```

仅管理员。

请求：

```json
{
  "name": "宫保鸡丁",
  "description": "经典川菜",
  "price": 28,
  "category_id": 1,
  "image_url": "https://static.myfeiniao.cn/recipes/a.jpg"
}
```

如果没有图片：

```json
{
  "image_url": null
}
```

---

## 13.4 修改菜谱

```http
PUT /api/recipes/{id}
```

仅管理员。

---

## 13.5 删除菜谱

```http
DELETE /api/recipes/{id}
```

仅管理员。

删除前应考虑订单历史关联。

推荐优先使用：

```text
status = inactive
```

进行下架。

---

# 14. 分类 API

查询：

```http
GET /api/categories
```

管理员：

```http
POST /api/categories
PUT /api/categories/{id}
DELETE /api/categories/{id}
```

普通用户只能：

```http
GET /api/categories
```

---

# 15. 订单 API

## 创建订单

```http
POST /api/orders
```

请求：

```json
{
  "items": [
    {
      "recipe_id": 1,
      "quantity": 2
    },
    {
      "recipe_id": 5,
      "quantity": 1
    }
  ]
}
```

后端处理：

```text
校验用户
 ↓
查询菜谱
 ↓
验证菜谱是否 active
 ↓
获取当前价格
 ↓
创建 orders
 ↓
创建 order_items
 ↓
保存下单时价格
 ↓
提交事务
```

必须使用数据库事务，保证：

```text
订单创建成功
+
订单明细创建成功
```

二者要么全部成功，要么全部失败。

---

## 我的订单

```http
GET /api/orders
```

只能返回当前用户自己的订单。

前端必须提供 `/orders` 页面展示当前用户的订单列表，并提供进入订单详情的入口。
页面不得依赖客户端传入的 `user_id` 判断归属；用户身份由登录 Token 和后端 SQL 过滤决定。

---

## 订单详情

```http
GET /api/orders/{id}
```

必须校验：

```text
order.user_id == current_user.id
```

管理员可以根据业务需要查看全部订单。

---

## 取消订单

```http
POST /api/orders/{id}/cancel
```

只能取消属于自己的订单，并且只允许符合条件的订单取消。

前端取消操作必须显示处理中状态，并在成功后刷新订单状态；后端返回 `409` 时必须保留页面并提示订单已不能取消。

## 点菜前端交互

菜谱详情页的“点菜”操作必须真正调用：

```http
POST /api/orders
```

请求体使用当前菜谱 ID 和数量：

```json
{
  "items": [
    {
      "recipe_id": 1,
      "quantity": 2
    }
  ]
}
```

数量控件的范围为 `1..99`，提交期间按钮必须禁用并显示处理中状态，避免重复提交。
成功后进入 `/orders/{id}` 或显示可访问的订单详情入口；`400`、`422`、`409` 和网络错误都必须显示可理解的错误信息。
按钮不能以“后续阶段开放”等占位逻辑永久禁用。

---

## 管理员修改订单状态

```http
PUT /api/admin/orders/{id}/status
```

仅管理员。

---

# 16. 前端路由设计

建议：

```text
/login

/recipes

/orders
/orders/:id

/admin/recipes
/admin/categories
/admin/orders
/admin/orders/:id
```

其中：

```text
/recipes
```

Admin 和 User 都可以访问。

区别：

```text
Admin:
新增 / 编辑 / 删除 / 上下架

User:
查看 / 筛选 / 点菜
```

---

# 17. 前端权限设计

已有：

```text
ProtectedRoute
```

继续增加：

```text
RoleRoute
```

例如：

```tsx
<RoleRoute roles={['admin']}>
    <AdminRecipes />
</RoleRoute>
```

普通用户访问：

```text
/admin/recipes
```

前端可以跳转：

```text
403
```

或：

```text
/recipes
```

但后端仍然必须检查权限。

---

# 18. 前端页面

## 18.1 菜谱列表

用户看到：

```text
菜谱
--------------------------------

[全部] [中餐] [西餐] [日料]

┌──────────────┐
│     图片      │
│              │
│  宫保鸡丁     │
│  ¥28          │
│  [点菜]       │
└──────────────┘

        1  2  3  下一页
```

---

## 18.2 菜谱详情

显示：

- 图片
- 名称
- 分类
- 描述
- 价格
- 点菜数量
- 点菜按钮

---

## 18.3 管理员菜谱管理

```text
菜谱管理

[新增菜谱]

名称 | 分类 | 价格 | 状态 | 操作
-------------------------------------
宫保鸡丁 | 中餐 | 28 | 上架 | 编辑 删除
牛排     | 西餐 | 58 | 下架 | 编辑 删除
```

---

## 18.4 新增/编辑菜谱

表单：

```text
菜谱名称
菜谱描述
价格
分类
图片上传
状态

[保存]
```

图片：

```text
未上传
→ 使用默认图
```

---

# 19. Redis 缓存方案

菜谱列表属于适合缓存的数据。

采用：

```text
Cache Aside
```

读取：

```text
GET /recipes

 ↓

Redis

 ↓ hit
直接返回

 ↓ miss

PostgreSQL

 ↓

Redis SET

 ↓

返回
```

Key 示例：

```text
recipes:page:1:size:10:category:2
```

TTL：

```text
60 秒
```

管理员修改菜谱后：

```text
DB 更新
 ↓
删除相关 Redis Cache
```

第一阶段不追求复杂的缓存精确失效，可先采用统一 recipes cache 清理。

---

# 20. 数据库事务

点菜必须使用事务：

```text
BEGIN
 ↓
创建 orders
 ↓
创建 order_items
 ↓
COMMIT
```

任何一步失败：

```text
ROLLBACK
```

菜谱、分类、订单更新等需要根据业务决定是否使用事务。

---

# 21. 后端代码结构

建议逐步调整成：

```text
backend/app/

├── api/
│   ├── auth.py
│   ├── tasks.py
│   ├── recipes.py
│   ├── categories.py
│   ├── orders.py
│   └── upload.py
│
├── services/
│   ├── oss.py
│   ├── recipe_service.py
│   └── order_service.py
│
├── core/
│   ├── config.py
│   └── security.py
│
├── db/
│   ├── connection.py
│   └── init.sql
│
└── main.py
```

原则：

```text
api
 ↓
service
 ↓
database
```

OSS 上传：

```text
api
 ↓
oss service
 ↓
OSS
```

---

# 22. 错误处理

统一返回合适 HTTP 状态：

```text
401 Unauthorized
未登录 / Token 无效

403 Forbidden
没有权限

404 Not Found
资源不存在

400 Bad Request
参数错误

422 Unprocessable Entity
请求结构/校验失败

500 Internal Server Error
服务器内部错误
```

例如：

普通用户删除菜谱：

```http
403
```

而不是：

```http
401
```

---

# 23. 数据安全

必须保证：

### 用户数据隔离

普通用户：

```sql
WHERE user_id = current_user.id
```

查询自己的订单。

---

### 菜谱管理员权限

```text
DELETE /recipes
```

必须：

```text
role == admin
```

---

### 图片上传

限制：

```text
image/jpeg
image/png
image/webp
```

建议增加文件大小限制。

第一版例如：

```text
<= 5MB
```

---

# 24. 执行顺序

严格按照以下顺序实现。

## Phase 1：角色系统

目标：

```text
users.role
 ↓
JWT role
 ↓
get_current_user
 ↓
require_admin
```

验证：

```text
admin → 管理接口成功
user  → 403
```

---

## Phase 2：分类系统

实现：

```text
recipe_categories
```

API：

```text
GET
POST
PUT
DELETE
```

完成管理员分类管理。

---

## Phase 3：菜谱 CRUD

实现：

```text
recipes
```

完成：

```text
GET
GET /{id}
POST
PUT
DELETE
```

加入：

```text
category_id
status
image_url
```

---

## Phase 4：OSS 图片上传

实现：

```text
POST /api/upload/image
```

完成：

```text
FastAPI
 ↓
OSS
 ↓
返回 image_url
```

验证：

- 上传图片成功
- OSS 中存在文件
- 返回 URL 可以访问
- 不上传图片时 image_url 为 null

---

## Phase 5：菜谱前端

完成：

```text
菜谱列表
分类筛选
分页
菜谱详情
```

---

## Phase 6：管理员菜谱管理

完成：

```text
新增
编辑
删除
上架
下架
图片上传
```

---

## Phase 7：订单系统

建立：

```text
orders
order_items
```

完成：

```text
点菜
我的订单
订单详情
取消订单
```

前端验收必须包括：

```text
菜谱详情页可以提交 POST /api/orders
提交期间不能重复提交
成功后可以进入订单详情
普通用户可以查看自己的订单列表和详情
普通用户可以取消符合条件的订单
页面正确处理 401/403/404/409/422 和网络错误
```

---

## Phase 8：管理员订单

完成：

```text
查看订单
修改订单状态
```

管理员前端页面建议提供：

```text
/admin/orders
/admin/orders/:id
```

管理员页面不能替代后端 `admin` 权限校验。

---

## Phase 9：Redis

对：

```text
GET /recipes
GET /categories
```

根据实际访问情况添加缓存。

---

## Phase 10：CI/CD 验证

每次：

```text
git push
```

执行：

```text
CI
 ├── frontend build
 ├── backend test
 └── lint

 ↓

CI通过

 ↓

CD

 ↓

ECS
```

---

# 25. 测试清单

## 权限

```text
[ ] user 不能新增菜谱
[ ] user 不能修改菜谱
[ ] user 不能删除菜谱
[ ] user 不能管理分类
[ ] user 不能查看其他用户订单
[ ] admin 可以管理菜谱
[ ] admin 可以管理分类
```

## 菜谱

```text
[ ] 新增菜谱
[ ] 编辑菜谱
[ ] 删除菜谱
[ ] 上架
[ ] 下架
[ ] 分类筛选
[ ] 分页
```

## 图片

```text
[ ] 上传 jpg
[ ] 上传 png
[ ] 上传 webp
[ ] 非图片文件被拒绝
[ ] 超大文件被拒绝
[ ] 图片成功进入 OSS
[ ] 返回 URL 正常访问
[ ] 不上传图片使用默认图
```

## 订单

```text
[ ] 正常点菜
[ ] 多个菜品点菜
[ ] 数量正确
[ ] 总金额正确
[ ] 保存下单时价格
[ ] 用户只能查看自己的订单
[ ] 可以取消符合条件的订单
[ ] 菜谱详情页“点菜”按钮可实际创建订单
[ ] 点菜请求提交期间按钮防重复提交
[ ] 创建成功后可进入订单详情
[ ] 普通用户订单列表和详情页面可用
[ ] 页面正确显示订单创建失败和取消失败
```

## 缓存

```text
[ ] Redis miss → DB
[ ] DB结果写入 Redis
[ ] Redis hit → 直接返回
[ ] 菜谱修改后缓存失效
```

---

# 26. 暂时不做的功能

第一阶段不实现：

```text
支付
购物车
优惠券
库存
配送
退款
评价
收藏
搜索引擎
CDN
OSS STS 前端直传
微服务
Kubernetes
```

保持项目范围可控。

---

# 27. 最终系统架构

```text
                    用户
                      │
                    HTTPS
                      ↓
                 ECS Nginx
                      │
              ┌───────┴────────┐
              ↓                ↓
           React             FastAPI
                                │
          ┌─────────────────────┼────────────────┐
          ↓                     ↓                ↓
      PostgreSQL              Redis             OSS
          │                     │                │
          │                     │                │
      users                    cache         recipes/*
      recipes
      categories
      orders
      order_items
```

CI/CD：

```text
开发者
  │
  │ git push
  ↓
GitHub
  │
  ↓
GitHub Actions
  │
  ├── CI
  │    ├── frontend build
  │    ├── backend test
  │    └── lint
  │
  ↓
CD
  │
  ↓
ECS
  │
  ↓
Docker Compose
```

---

# 28. AI 执行原则

后续让 AI 执行本方案时，必须遵循：

1. **一次只完成一个 Phase**
2. 每完成一个 Phase，必须可以本地运行和验证
3. 修改现有代码前先分析现有目录和相关实现
4. 不随意修改已经正常工作的功能
5. 数据库变更必须明确 SQL
6. API 变更必须明确请求和响应结构
7. 后端权限必须真实校验，不能只实现前端权限
8. OSS AccessKey 不得写入前端代码
9. 每个 Phase 完成后提供验证命令
10. 未完成当前 Phase 前，不进入下一 Phase
11. 出现错误时先定位根因，不通过大范围重构解决问题
12. 保持现有 Docker、Nginx、CI/CD 部署方式兼容

---

# 29. 第一阶段执行目标

当前第一阶段只做：

```text
users 增加 role
        ↓
JWT 增加 role
        ↓
get_current_user 获取 role
        ↓
require_admin
        ↓
验证 admin / user 权限
```

完成标准：

```text
admin 登录
    ↓
获得 role=admin
    ↓
可以访问管理员接口

user 登录
    ↓
获得 role=user
    ↓
访问管理员接口
    ↓
403 Forbidden
```

**第一阶段完成并验证通过后，才开始 Phase 2 分类系统。**

---

# 30. 生产数据库迁移迭代方案

## 30.1 现状和问题

`backend/app/db/init.sql` 当前通过 Docker Compose 挂载到：

```text
/docker-entrypoint-initdb.d/init.sql
```

PostgreSQL 只会在数据卷第一次初始化时执行该目录中的脚本。已有生产数据卷不会因为修改 `init.sql`、重新构建镜像或执行 `docker compose up -d --build` 而重新执行脚本。

因此：

```text
修改 init.sql
        ↓
重新 build
        ↓
已有 PostgreSQL 数据卷
        ↓
不会自动升级表结构
```

禁止通过删除数据卷解决此问题。`docker compose down -v` 会删除数据库持久化数据，只能作为明确的数据重建操作，不能作为生产迁移手段。

## 30.2 目标架构

采用以下过渡方案：

```text
init.sql
  └── 只负责新数据库 bootstrap，作为冻结基线

backend/app/db/migrations/
  ├── V001__baseline_existing_schema.sql
  ├── V002__add_xxx.sql
  └── V003__add_xxx.sql

schema_migrations
  └── 记录已执行版本、执行时间和 checksum
```

今后的生产表结构变化只能通过版本化 migration SQL 完成，不能只修改 `init.sql`。

不引入 ORM 自动建表，也不要求当前项目为了迁移强行引入 Alembic。第一版使用项目已有的 `psycopg` 实现轻量 migration runner，保持 Docker、Compose 和现有数据库连接方式兼容。

## 30.3 迁移记录表

迁移 runner 首次运行时必须幂等创建以下记录表：

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(100) PRIMARY KEY,
    checksum CHAR(64) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

每条 migration 使用唯一版本号。已执行版本再次运行时必须比较 checksum：

```text
版本存在 + checksum 相同 → 跳过
版本存在 + checksum 不同 → 立即失败
版本不存在             → 执行 SQL，成功后记录
```

不能静默覆盖已经执行过的 migration 文件。

## 30.4 首次上线迁移

当前生产数据库已经存在：

```text
users
tasks
recipe_categories
recipes
orders
order_items
```

首次迁移不能把生产库当作空库处理。迁移步骤必须是：

1. 备份生产数据库，例如执行 `pg_dump -Fc`，并验证备份文件可读取。
2. 检查现有表、字段、类型、默认值、外键、索引、约束和数据量。
3. 创建 `schema_migrations`。
4. 执行或核对 `V001__baseline_existing_schema.sql`。
5. 只有实际结构符合当前方案时，才登记 V001；结构不一致必须停止并人工处理。
6. 验证应用登录、Task、菜谱、订单和 Redis 连接。

V001 必须是幂等的，并保护已有用户、任务、菜谱、订单和订单明细。不能在 V001 中删除业务数据，也不能用空库重建覆盖生产库。

## 30.5 新增结构的规则

以后每次数据库迭代必须新增文件，例如：

```text
V002__add_recipe_sort_order.sql
V003__add_order_completed_at.sql
```

每个 migration 文件必须包含：

```text
唯一版本号
明确 SQL
变更目的
前置结构假设
兼容性说明
回滚/恢复说明
```

推荐使用向前兼容的 expand/contract 顺序：

```text
先增加可空字段或新表
        ↓
发布兼容旧结构和新结构的应用
        ↓
回填并验证数据
        ↓
再切换读写逻辑
        ↓
最后单独发布删除旧字段的 migration
```

涉及删除字段、重命名字段、修改类型、唯一约束或大量回填时，必须单独评估锁表时间、数据量和回滚方式。migration runner 默认不执行自动 down migration；回滚优先使用应用版本回退、备份恢复或新的修复 migration。

## 30.6 Migration Runner 要求

建议入口：

```text
python -m app.db.migrate
```

runner 必须：

1. 从 `DATABASE_URL` 读取数据库连接，不读取前端配置。
2. 按版本号排序读取 migrations 目录。
3. 使用 PostgreSQL advisory lock 防止多个发布进程并发迁移。
4. 每个 migration 在独立事务中执行。
5. SQL 成功提交后再写入 `schema_migrations`。
6. 任意 migration 失败立即退出非零状态，不继续后续版本。
7. 检测 checksum 漂移并拒绝启动。
8. 支持只读检查或 status 输出，不能把检查模式误当成执行模式。
9. 日志只输出版本、耗时和结果，不输出密码、Token 或 OSS AccessKey。

## 30.7 生产发布顺序

ECS 发布顺序必须调整为：

```text
git pull --ff-only
        ↓
备份 PostgreSQL
        ↓
确认 postgres healthy
        ↓
执行 migration runner
        ↓
检查 schema_migrations 和关键表结构
        ↓
docker compose up -d --build backend frontend
        ↓
执行健康检查和 API 冒烟测试
```

推荐将迁移作为一次性 Compose job 或独立发布步骤：

```text
docker compose run --rm backend python -m app.db.migrate
```

实际命令必须使用项目镜像内的依赖和生产环境变量。migration 成功前不能切换到依赖新结构的后端版本。

## 30.8 CI/CD 门禁

CI 必须至少验证：

```text
空数据库执行全部 migrations 成功
同一批 migrations 第二次执行无变化
已执行版本 checksum 被修改时失败
任意 migration 失败时后续版本不执行
应用测试数据库结构与生产基线一致
```

CD 必须验证：

```text
迁移 job 成功后才更新 backend
迁移失败时部署退出非零状态
已有 PostgreSQL 数据卷未被删除
schema_migrations 记录完整
```

Phase 10 在迁移 runner、生产发布顺序和 CI/CD 门禁完成前不能标记为 complete。
