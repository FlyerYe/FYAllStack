# FYAllStack

一个基于 **React + TypeScript + FastAPI + PostgreSQL + Docker** 构建的全栈业务系统。

项目从基础任务管理系统演进，逐步实现用户认证、JWT 鉴权、RBAC 权限控制、菜谱管理、OSS 图片上传、Docker 容器化部署以及 GitHub Actions 自动化部署流程。

目标是构建一个接近真实生产环境的前后端分离应用，覆盖完整的软件开发生命周期：

> 开发 → 数据设计 → 服务部署 → 自动化发布 → 线上运行

测试账号：fuye
测试密码：123321
---

# 项目架构

整体采用前后端分离架构：

```
                 用户浏览器

                     |
                     ↓

                Nginx 网关

                     |
          ---------------------

          ↓                   ↓

      React 前端          FastAPI 后端
      Docker              Docker


                              |
              --------------------------------

              ↓              ↓              ↓

        PostgreSQL        Redis          OSS
        数据存储          缓存        图片存储
```

---

# 技术栈

## 前端

- React
- TypeScript
- Vite
- Axios
- React Router
- JWT Token 管理


## 后端

- Python
- FastAPI
- Pydantic
- JWT Authentication
- RESTful API


## 数据库

- PostgreSQL
- SQL
- 数据迁移管理


## 缓存

- Redis


## 文件存储

- 阿里云 OSS


## 部署

- Docker
- Docker Compose
- Nginx
- GitHub Actions
- 阿里云 ECS

---

# 已实现功能

## 1. 用户认证系统

支持：

- 用户注册
- 用户登录
- JWT Token 登录态管理
- Token 校验
- Token 过期处理


认证流程：

```
用户登录

    ↓

FastAPI 校验账号密码

    ↓

生成 JWT Token

    ↓

客户端保存 Token

    ↓

请求携带 Authorization Header

    ↓

后端解析用户身份
```

---

# 2. RBAC 权限系统

实现基于角色的访问控制：

```
             用户

              |

            role

        /           \

     admin          user

      |              |

 管理功能        普通功能
```


角色：

|角色|权限|
|-|-|
|admin|菜谱管理、图片上传等后台能力|
|user|浏览菜谱、点餐等用户能力|


权限控制由后端负责：

- 前端控制展示
- 后端校验权限

避免仅依赖前端造成安全问题。

---

# 3. 任务管理系统（作为练手，暂时隐藏）

基础业务模块：

支持：

- 创建任务
- 查询任务
- 修改任务
- 删除任务


用户数据隔离：

```
用户A

只能访问

user_id=A 的数据
```

后端通过当前登录用户身份限制数据访问。

---

# 4. 菜谱管理系统

支持：

- 菜谱分类
- 菜谱创建
- 菜谱编辑
- 菜谱状态管理
- 图片上传


业务模型：

```
recipe_categories

        |

        |

      recipes
```


菜谱信息：

|字段|说明|
|-|-|
|name|菜名|
|description|描述|
|price|价格|
|category_id|分类|
|image_url|图片地址|
|status|状态|

---

# 5. OSS 图片上传

采用后端代理上传模式：

```
管理员

 ↓

React 上传图片

 ↓

FastAPI

 ↓

阿里云 OSS

 ↓

返回图片 URL

 ↓

保存数据库
```


设计原则：

- OSS AccessKey 不暴露给前端
- 后端统一控制上传权限
- 图片类型校验
- 文件大小限制
- UUID 文件路径避免文件冲突


图片存储：

```
recipes/

    uuid.jpg
```

---

# 6. 数据库迁移机制

项目支持数据库结构持续演进。

解决：

> PostgreSQL init.sql 不会在已有数据库中重复执行的问题。


采用 migration 管理：

```
migrations/

001_init.sql

002_add_user_role.sql

003_add_recipe_tables.sql
```


通过版本记录保证：

- 数据库结构可追踪
- 避免重复执行
- 支持线上升级

---

# 7. Docker 容器化

项目支持 Docker Compose 一键启动：

```bash
docker compose up -d --build
```


服务：

```
frontend

backend

postgres

redis
```


优势：

- 开发环境一致
- 部署流程标准化
- 降低环境差异问题

---

# 8. Nginx 网关

线上通过 Nginx 统一入口：

```
用户

 ↓

Nginx

 ↓

----------------

frontend

backend API
```


负责：

- 静态资源代理
- API 转发
- HTTPS
- 前后端统一入口

---

# 9. CI/CD 自动部署

使用 GitHub Actions 实现自动部署：

流程：

```
代码提交

    ↓

GitHub Actions

    ↓

CI持续集成校验

    ↓
CD持续部署

    ↓

SSH 登录 ECS

    ↓

拉取最新代码

    ↓

Docker Build

    ↓

重新部署服务
```


实现：

- 自动化校验、发布
- 减少人工操作
- 保证部署流程一致

---

# 项目目录

```
FYAllStack

├── frontend
│   ├── React
│   └── TypeScript
│

├── backend
│   ├── FastAPI
│   ├── API
│   ├── Service
│   └── migrations
│

├── docker-compose.yml

├── nginx

└── .github
    └── workflows
        └── deploy.yml
```

---

# 本地运行

## 1. 启动基础服务

启动 PostgreSQL、Redis：

```bash
docker compose up -d postgres redis
```

---

## 2. 启动后端

```bash
cd backend

uv run uvicorn app.main:app --reload
```


访问：

```
http://localhost:8000/docs
```

---

## 3. 启动前端

```bash
cd frontend

npm install

npm run dev
```


访问：

```
http://localhost:5173
```

---

# 生产部署

服务器环境：

- Linux ECS
- Docker
- Nginx


部署流程：

```
GitHub

 ↓

Actions

 ↓

ECS

 ↓

Docker Compose

 ↓

应用上线
```

---

# 项目亮点

## 1. 全链路实践

覆盖：

- 前端开发
- 后端 API
- 数据库设计
- 权限系统
- 文件存储
- 容器化
- 自动部署


## 2. 接近生产环境设计

包含：

- JWT 鉴权
- RBAC 权限
- Migration 数据管理
- OSS 文件管理
- CI/CD


## 3. 可持续扩展

后续可扩展：

- docker镜像版本管理
- accesss token +refresh token
- 增加ECS deploy账号
- 其他

---

# License

MIT