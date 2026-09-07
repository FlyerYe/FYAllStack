---
name: recipe-order-system

description: "按照 recipe-order-system-design.md，在现有 FYAllStack 项目中分阶段实施菜谱与点餐系统；每次只执行一个经过实际验证的 Phase。仅当该方案文件存在时使用，不执行无关重构，也不一次性实现完整项目。"

---

# 菜谱与点餐系统实施 Skill

本 Skill 用于安全、渐进地执行项目根目录中的 `recipe-order-system-design.md`。该方案文件是产品需求和实施顺序的依据；现有仓库代码是当前目录结构、接口契约、配置和部署行为的唯一事实来源。

## 不可违反的范围

- 必须在仓库根目录工作。先执行 `git rev-parse --show-toplevel`，并确认根目录存在 `recipe-order-system-design.md`。
- 在实现前完整读取 `recipe-order-system-design.md`。修改代码前重新读取当前 Phase 及其相关的 API、数据、安全和验收章节。
- 修改前必须检查现有实现及其所有调用方。不得凭空假设文件、模块、数据表、接口、环境变量或类型已经存在。
- 默认每次调用只执行一个 Phase。不得在当前 Phase 未完成和未验证时实现后续 Phase。只有用户明确要求继续时，才可以在当前 Phase 验证并记录进度后开始下一个 Phase；即使继续，也不能跳过每个 Phase 的验证。
- 变更必须严格限定在当前 Phase。不得借 Phase 之名进行无关重构、依赖升级、格式化噪音或工作中 Task 功能的重新设计。
- 必须保持已有功能可用。尤其是在修改共享鉴权或数据库代码后，必须验证已有 Task 和登录流程；出现回归时立即停止推进。
- 任何必要验证失败后，必须停留在当前 Phase，先定位和修复当前问题，不得开始新的 Phase，也不得用大范围重写掩盖失败。
- 未经用户明确要求，不得执行 `git commit`、`git push`、`git reset`、`git checkout --`、`git clean` 等可能改变用户 Git 历史、丢失工作内容或覆盖用户修改的操作。

## 仓库状态与进度

使用仓库根目录的 `recipe-order-system-progress.md` 作为执行账本。该文件记录方案实施状态，不是 Skill 本身的说明文件。

每次调用开始时必须：

1. 如果存在，先读取进度文件。

2. 如果不存在，推断 `current_phase: 1`，报告方案尚未开始，并先创建初始进度记录。初始化模式不得直接实现 Phase 1。第一次运行 Skill 必须只完成初始化；只有后续用户明确要求执行时，才可以开始 Phase 1。

3. 执行 `git status --short`，识别用户已有修改。保留用户修改，不得回滚无关变更。如果工作区存在与当前 Phase 无关的未提交修改，只要不会覆盖、删除或破坏这些修改，就不得要求用户先提交、清理或重置工作区；应继续执行当前 Phase。

4. 只有进度账本中记录的当前 Phase 可以实施。标记为完成的 Phase 必须包含实际执行的命令及结果，不能只写计划。

进度文件至少包含：

```text
# Recipe Order System Progress

- status: not_started | in_progress | blocked | complete
- current_phase: 1..10
- current_phase_name: ...
- completed_phases: []
- completed_work: ...
- modified_files: []
- database_sql: ...
- validation_commands: []
- validation_result: not_run | passed | failed
- open_issues: ...
- next_step: ...
```

文件路径使用相对仓库根目录的路径。进度文件中绝对不能写入密钥、AccessKey、Token、密码或完整的私有环境变量值。

## 执行模式

### 初始化

初始化只建立上下文，不实现业务：

- 完整读取方案文件，识别十个 Phase、当前验收标准、安全规则和明确暂不实现的功能。
- 盘点实际源码树、依赖清单、测试、环境示例、数据库初始化方式、Docker Compose、Nginx 和 GitHub Actions。
- 读取已有进度文件，或创建 `not_started`/Phase 1 初始记录。
- 初始化期间不得添加菜谱、分类、订单、迁移、路由、组件、依赖或业务逻辑。
- 如果本次调用只是初始化，不得在初始化结束后顺便开始 Phase 1。

### 执行当前 Phase

编辑前必须先报告：

- 当前 Phase 及方案文件中的验收标准。
- 将要检查或修改的文件和符号。
- 工作区中与本 Phase 重叠的用户修改。
- 从前端调用方、API 路由、Service、数据库/缓存/存储到部署配置的完整请求链路。
- 最小兼容实现方案，以及仓库无法证明时明确标注的假设。

然后只实现当前 Phase。除非当前 Phase 有明确要求，否则保持现有 API、Service、数据库和部署边界。

### 验证与更新进度

验证是 Phase 的组成部分，不能作为可选的后续工作：

- 必须针对当前项目执行真实命令，包括受影响的聚焦测试，以及相关的前端构建、Lint、后端编译、测试或集成检查。
- 优先使用仓库已有工具链，例如 `npm`、`uv`、仓库已有的 `pytest` 和 `docker compose`。不得仅为方便而凭空引入新的测试框架。
- 数据库变更必须同时验证 SQL 和可用 PostgreSQL 的实际表结构。如果数据库不可用，必须说明限制，不能宣称该 Phase 已完全验证。
- API 变更必须验证成功、未登录、无权限、参数校验、资源不存在、资源归属等当前 Phase 涉及的路径。
- 图片上传必须在条件允许时验证类型拒绝、大小拒绝、URL 返回、OSS 文件存在/可访问和无图片路径。
- 共享基础设施变更后必须验证已有 Task 行为及受影响的部署契约。
- 只有全部必要检查通过后，才能把当前 Phase 加入 `completed_phases`、设置 `validation_result: passed`、记录下一 Phase、修改文件和实际命令。失败时将 `status` 设为 `blocked`，保留当前 Phase，记录失败和定位结果，不得推进。

### 继续执行

用户明确要求继续时，重新读取进度文件，只开始其中记录的下一个 Phase。上一 Phase 通过不代表可以跳过下一 Phase 的代码检查。如果用户只说“执行方案”而没有明确指定继续，则只执行当前 Phase。

## 跨阶段安全规则

### 鉴权与权限

- 后端是实际安全边界。前端路由、菜单、按钮或 localStorage 检查都不能代替后端授权。
- 修改 JWT 或当前用户处理逻辑前，必须检查现有 Token 创建、解析、`OAuth2PasswordBearer`、依赖调用方、过期配置和响应契约。
- 除非兼容性分析和方案明确要求，否则保留现有 `sub` 和过期语义。在后端增加并校验 `role`，不得信任前端提交的角色。
- 已有鉴权 Task 接口必须继续工作。如果改变 `get_current_user` 的返回结构，必须明确更新所有调用方并进行验证。
- 已登录但不是管理员的用户访问管理员接口必须返回 `403 Forbidden`；未登录、Token 无效或过期必须返回 `401 Unauthorized`。不能混淆两种情况。
- 用户资源必须在后端 SQL 和 Service 中按当前认证用户 ID 过滤，不能使用客户端传入的 owner ID 作为安全依据。
- 不得通过未保护的公开注册接口创建管理员。如果需要管理员初始化或提升，必须提供明确的受保护 SQL，并且不能放进前端代码。

### 数据库与 SQL

- 修改任何表前，必须检查仓库 SQL 和实际 PostgreSQL 结构，包括表、字段、类型、可空性、默认值、外键、索引及相关数据。不能假设数据库为空。
- 必须检查 `backend/app/db/init.sql` 的应用方式以及 Compose 数据卷是否已经初始化。注意 PostgreSQL 初始化脚本不会在已有数据卷上自动重新执行。
- `backend/app/db/init.sql` 只用于新数据库 bootstrap；生产数据库升级必须使用版本化 migration SQL 和可审计的 migration runner，不能因为修改 `init.sql` 就宣称线上结构已升级。
- 任何版本化 migration 必须记录版本、执行时间和 checksum；已执行版本内容发生变化时必须失败，不能静默覆盖。迁移前必须备份并检查实际结构，禁止通过 `docker compose down -v` 代替迁移。
- 所有数据库变化都必须有明确、可审查的 SQL，并在最终报告中列出。优先采用与当前项目兼容的幂等迁移或明确迁移步骤，不能默默依赖 ORM 自动迁移。
- 如果当前项目尚未建立正式数据库迁移工具，不得为了当前 Phase 擅自引入 Alembic 或其他迁移框架；应优先采用与现有 `init.sql`、数据库初始化和 Compose 运行方式兼容的迁移方案，并明确告诉用户生产数据库需要执行的 SQL。
- 每个数据库变更都要说明兼容性、回滚考虑和已有数据保护方式，尤其不能破坏已有 users 和 tasks 数据。
- `orders` 和 `order_items` 必须在同一个数据库事务中创建。`order_items.price` 必须保存下单时的不可变价格快照，后续菜谱价格变化不能影响历史订单。
- 必须区分菜谱下架和物理删除。优先通过 `active`/`inactive` 表示停止售卖；物理删除前必须检查订单历史外键，不能破坏历史语义。

### API 契约

每个新增或修改的接口都必须说明并验证：

- HTTP 方法和准确路径，包括当前项目 `/api` 前缀的实际行为。
- Query、Path、Header、JSON 和 multipart 字段，以及字段校验规则。
- 成功响应的状态码和 JSON 结构，以及相关错误响应。
- 是否需要登录、所需角色和资源归属规则。
- 是否兼容现有前端和其他调用方。

路由已注册、响应行为已实际测试前，不得声称接口已经实现。

### OSS 与图片上传

- 修改 OSS 前，必须检查现有配置加载、`.env.example`、Docker 环境传递以及已有文件存储/上传实现。
- OSS 凭据只能由后端读取。AccessKey、Secret、Bucket 凭据和特权存储操作不得出现在前端源码、Vite 暴露变量、提交产物或日志中。
- 图片类型只允许 `image/jpeg`、`image/png`、`image/webp`，并执行方案指定的大小限制，第一版默认上限为 5 MB。必须安全拒绝不支持或异常内容。
- 对象键由后端生成 UUID，统一放在 `recipes/` 目录；不能直接使用用户原始文件名。
- 图片上传是可选的。没有图片时保存 `image_url = null`，前端使用默认图片。
- 必须进行针对性的敏感信息暴露检查，但不得打印密钥内容。

### Redis 与部署

- 修改缓存前，必须检查 `backend/app/db/redis.py`、现有缓存键、TTL、失效逻辑、配置和所有调用方。缓存键必须维持用户数据隔离。
- 只在当前 Phase 需要时增加 Cache Aside。菜谱或分类写操作后必须使相关缓存失效，不能引入跨用户、跨状态的脏数据。
- 必须保持 Docker Compose 服务名、健康检查、环境变量传递、Nginx SPA fallback、`/api/` 代理和容器构建上下文可用。
- 必须保持 GitHub Actions CI/CD 可用，不能为了通过 Phase 而降低检查或部署步骤。`.env` 和凭据必须保持不被 Git 跟踪，提交配置只能包含安全示例。
- 发布流程中，依赖新表结构的应用更新前必须先执行未应用 migration；migration 失败时停止发布。CI 必须验证空库执行、重复执行、checksum 漂移和失败即停。

## Phase 门禁

严格使用方案文件中的顺序和验收标准：

1. 角色系统：`users.role`、JWT role、当前用户角色、`require_admin`，以及 admin/user 的权限验证。

2. 分类系统：普通用户读取和管理员 CRUD，包含数据库约束和后端授权。

3. 菜谱 CRUD：分类、价格、状态、可选图片 URL、分页/筛选，以及安全的删除/下架语义。

4. OSS 图片上传：后端存储、UUID 对象键、MIME 和大小校验、URL 返回及默认图片路径。

5. 菜谱前端：列表、分类筛选、分页、详情、加载/错误/空状态和点菜入口。

6. 管理员菜谱管理：新增、编辑、删除或下架、状态切换、图片上传和角色保护路由。

7. 订单系统：事务性的 `orders`/`order_items`、上架菜谱校验、数量/总价校验、价格快照、用户订单隔离、详情和取消规则。

8. 管理员订单：按设计授权查看订单及安全修改订单状态。

9. Redis：菜谱/分类的 Cache Aside、TTL、键隔离和写操作失效。

10. CI/CD 验证：前端构建、后端测试/编译、Lint、Compose/部署兼容性和现有 GitHub Actions 流程。

方案明确暂不实现：支付、购物车、优惠券、库存、配送、退款、评价、收藏、搜索引擎、CDN、OSS STS 前端直传、微服务和 Kubernetes。不得把这些功能混入当前 Phase。

## 每次输出格式

每次修改或验证后，都必须使用用户的语言输出以下内容：

```text
当前 Phase：

实施计划：

修改文件：

数据库 SQL：

API 请求、响应与权限：

实际执行的命令：

测试/验证结果：

当前状态：

下一步建议：
```

状态必须明确使用 `not_started`、`in_progress`、`blocked` 或 `complete`。要区分已经实际执行的命令和仅建议执行的命令，记录失败和遗留风险。当前 Phase 阻塞或未验证时，绝不能报告后续 Phase 已完成。

## 当前仓库检查起点

以下路径是在创建本 Skill 时发现的起点，不是可以跳过检查的假设；每次运行都必须重新确认：

- 后端：`backend/app/api/auth.py`、`backend/app/api/tasks.py`、`backend/app/core/security.py`、`backend/app/core/config.py`、`backend/app/db/init.sql`、`backend/app/db/redis.py` 和 `backend/app/services/`。
- 前端：`frontend/src/App.tsx`、`frontend/src/components/ProtectedRoute.tsx`、`frontend/src/utils/request.ts`、`frontend/src/api/` 和 `frontend/src/pages/`。
- 运行与部署：`docker-compose.yml`、`backend/Dockerfile`、`frontend/Dockerfile`、`frontend/nginx.conf`、`.env.example` 和 `.github/workflows/deploy.yml`。

当前仓库已有 Task、登录鉴权、Redis 缓存和部署流程，这些共享功能容易被后续修改破坏。在实际检查和验证证明兼容之前，必须把它们视为不可随意改变的边界。
