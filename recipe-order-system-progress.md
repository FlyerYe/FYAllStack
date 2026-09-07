# Recipe Order System Progress

- status: in_progress
- current_phase: 10
- current_phase_name: CI/CD 验证
- completed_phases: [1, 2, 3, 4, 5, 6, 7, 8, 9]
- completed_work: |
    Phase 1 已完成：users.role、JWT role、当前用户对象和 require_admin 已实现。
    普通注册用户默认是 user；管理员角色需要通过受保护的数据库初始化/管理流程设置，不能通过公开注册接口创建。
    Task 路由已适配新的当前用户对象，仍按 current_user.user_id 执行数据隔离。
    Phase 2 已完成：recipe_categories 表、分类 Schema/Service/API 已实现并注册。
    GET /api/categories 需要登录，普通用户和管理员均可查询；POST/PUT/DELETE 仅管理员可用。
    分类名称会去除首尾空格，数据库唯一约束和 API 冲突处理已验证。
    Phase 3 已完成：recipes 表、菜谱 Schema/Service/API 已实现并注册。
    普通用户只能查询 active 菜谱；管理员可查看全部状态并按 status/category_id 筛选。
    菜谱新增、修改、物理删除仅管理员；PUT status=inactive 用于下架，DELETE 与下架保持区分。
    已验证价格、分类外键、状态约束、分页、分类筛选、用户可见性和管理员权限。
    Phase 4 已实现后端 OSS 图片上传链路：配置、oss2 SDK、UUID 对象键、MIME/内容签名/5 MB 大小校验、管理员权限和返回图片 URL。
    OSS_ENDPOINT 已统一配置为 https://oss-cn-hongkong.aliyuncs.com；static.myfeiniao.cn 仅作为 OSS_DOMAIN 返回图片访问 URL。
    Phase 4 真实验收通过：管理员上传返回 200，OSS 对象存在，自定义域名 URL 返回 200，临时对象已删除；未登录和普通用户分别返回 401/403。
    Phase 5 已完成：受保护的菜谱列表、分类筛选、分页、菜谱详情、加载/错误/空状态和点菜入口已实现。
    菜谱前端复用后端的登录鉴权和 GET /api/categories、GET /api/recipes、GET /api/recipes/{id}；普通用户的上架可见性仍由后端强制保证。
    image_url 为 null 或图片加载失败时，前端使用本地默认菜谱图片。菜谱详情页提供 1..99 数量控件并实际创建订单，成功后进入用户订单详情。
    Phase 6 已完成：新增管理员菜谱管理页，支持新增、编辑、物理删除、上架/下架与图片上传；管理员菜谱列表包含所有状态。
    管理员路由仅在 JWT payload role=admin 时显示和渲染，普通用户会回到菜谱列表；后端 require_admin 仍是创建、修改、删除和上传的实际安全边界。
    Phase 6 问题修复：当 recipe_categories 为空时，管理员页提供新增分类入口；创建成功后自动刷新分类并选中新分类，之后可以直接提交菜谱。
    Phase 7 已完成：后端订单事务和用户隔离已实现，前端点菜入口已接通 POST /api/orders。
    订单只允许购买 active 菜谱，校验数量范围和重复菜谱；order_items.price 保存下单时价格快照，total_amount 从明细快照计算。
    普通用户的订单列表、详情和取消接口均按当前认证用户隔离；只有 pending 订单可以取消。
    Phase 7 真实 TestClient 订单验证、完整后端回归、编译、前端 lint/build、Compose 配置和 git diff --check 均已通过；测试临时数据已清理。
    普通用户已具备 /orders 和 /orders/:orderId 页面，可查看自己的价格快照订单并取消 pending 订单；提交期间会防止重复点菜。
    管理员接口统一使用后端 require_admin；普通用户和未登录请求分别返回 403/401，管理员可查看全部用户订单。
    订单状态只允许 pending 变为 completed 或 cancelled，已完成/已取消订单不可再次修改；新增管理员订单列表和详情页面。
    Phase 8 真实 TestClient 管理员权限/状态流转验证、完整后端回归、前端 lint/build、OpenAPI、Compose 配置和 git diff --check 均已通过；测试临时数据已清理。
    Phase 9 已完成：分类列表、菜谱列表和菜谱详情接入 Cache Aside；缓存键包含版本、资源、角色及查询条件，管理员和普通用户缓存隔离。
    缓存统一使用 JSON 和可配置 TTL（默认 60 秒）；Redis 读写异常或缓存损坏时回源数据库，不阻断业务接口。
    分类和菜谱新增、修改、删除会清理相关分类、菜谱列表和详情缓存；既有 Task 的 tasks:user:{user_id} 缓存键未改变。
    Phase 9 真实 Redis/PostgreSQL 集成测试、完整后端回归、前端 lint/build、编译、Compose 配置和 git diff --check 均已通过；项目缓存测试键已清理。
    数据库迭代方案已补充：init.sql 仅作为新库 bootstrap，生产升级改用版本化 migration SQL、schema_migrations、checksum、事务和 advisory lock；现网迁移 runner 及 CI/CD 发布步骤尚未实施。
- modified_files:
    - backend/app/api/auth.py
    - backend/app/api/tasks.py
    - backend/app/core/security.py
    - backend/app/db/init.sql
    - backend/tests/test_roles.py
    - backend/app/api/categories.py
    - backend/app/services/category_service.py
    - backend/app/schemas/categories.py
    - backend/app/main.py
    - backend/tests/test_categories.py
    - backend/app/api/recipes.py
    - backend/app/services/recipe_service.py
    - backend/app/schemas/recipes.py
    - backend/tests/test_recipes.py
    - backend/app/core/config.py
    - backend/app/api/upload.py
    - backend/app/services/oss.py
    - backend/app/schemas/upload.py
    - backend/pyproject.toml
    - backend/uv.lock
    - .env.example
    - docker-compose.yml
    - frontend/src/App.tsx
    - frontend/src/pages/Login.tsx
    - frontend/src/api/categories.ts
    - frontend/src/api/recipes.ts
    - frontend/src/pages/Recipes.tsx
    - frontend/src/pages/RecipeDetail.tsx
    - frontend/src/pages/recipes.css
    - frontend/src/assets/default-recipe-image.jpg
    - frontend/src/utils/auth.ts
    - frontend/src/components/AdminProtectedRoute.tsx
    - frontend/src/api/upload.ts
    - frontend/src/pages/AdminRecipes.tsx
    - backend/app/api/orders.py
    - backend/app/services/order_service.py
    - backend/app/schemas/orders.py
    - backend/tests/test_orders.py
    - frontend/src/api/orders.ts
    - frontend/src/pages/AdminOrders.tsx
    - frontend/src/pages/AdminOrderDetail.tsx
    - frontend/src/pages/orders.css
    - frontend/src/pages/Orders.tsx
    - frontend/src/pages/OrderDetail.tsx
    - backend/app/services/cache_service.py
    - backend/tests/test_cache.py
    - .env.example
    - docker-compose.yml
    - recipe-order-system-design.md
    - .codex/skills/recipe-order-system/SKILL.md
    - recipe-order-system-progress.md
- database_sql: |
    ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20);
    UPDATE users SET role = 'user' WHERE role IS NULL;
    ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user';
    ALTER TABLE users ALTER COLUMN role SET NOT NULL;
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'users_role_check'
              AND conrelid = 'users'::regclass
        ) THEN
            ALTER TABLE users
            ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'user'));
        END IF;
    END $$;
    已在项目配置的 todo_db 中执行并验证；2 条历史用户均回填为 user，未删除用户数据。
    CREATE TABLE IF NOT EXISTS recipe_categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    已在项目配置的 todo_db 中执行并验证；表结构、主键、name 唯一约束均存在，当前分类数量为 0。
    CREATE TABLE IF NOT EXISTS recipes (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price NUMERIC(10, 2) NOT NULL DEFAULT 0,
        image_url VARCHAR(500),
        category_id INTEGER NOT NULL REFERENCES recipe_categories(id),
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT recipes_status_check CHECK (status IN ('active', 'inactive'))
    );
    CREATE INDEX IF NOT EXISTS recipes_category_status_idx
    ON recipes (category_id, status);
    已在项目配置的 todo_db 中执行并验证；recipes 表、分类外键、状态检查约束和索引均存在，当前菜谱数量为 0。
    Phase 4：无数据库变更，无需 SQL。
    Phase 5：无数据库变更，无需 SQL。
    Phase 6：无数据库变更，无需 SQL。
    Phase 8：无数据库变更，复用 Phase 7 已验证的 orders/order_items 结构。
    Phase 7 前端补齐：无数据库变更，复用现有订单 API 和 orders/order_items 结构。
    Phase 9：无数据库变更，复用现有 Redis 服务和客户端；新增 CACHE_TTL_SECONDS 配置。
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT orders_status_check
            CHECK (status IN ('pending', 'completed', 'cancelled'))
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id SERIAL PRIMARY KEY,
        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        recipe_id INTEGER NOT NULL REFERENCES recipes(id),
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        price NUMERIC(10, 2) NOT NULL CHECK (price >= 0)
    );
    CREATE INDEX IF NOT EXISTS orders_user_id_created_at_idx
    ON orders (user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS order_items_order_id_idx
    ON order_items (order_id);
    已在项目配置的 todo_db 中执行并验证；保留已有 users/recipes 数据，订单测试临时数据已清理。
- validation_commands:
    - backend/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
    - backend/.venv/bin/python -m compileall -q app tests
    - backend/.venv/bin/python -c 'from app.main import app; ... app.openapi() ...'
    - npm run lint
    - npm run build
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m unittest tests.test_orders -v
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m unittest discover -s tests -p 'test_*.py' -v
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m compileall -q app tests
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -c 'from app.main import app; ... order routes ...'
    - PostgreSQL schema inspection for orders/order_items, foreign keys, constraints and indexes
    - PostgreSQL cleanup inspection for order test users, categories, recipes and orders
    - git diff --check
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m unittest tests.test_orders -v
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m unittest discover -s tests -p 'test_*.py' -v
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m compileall -q app tests
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -c 'from app.main import app; ... admin order routes ...'
    - PostgreSQL cleanup inspection for Phase 8 order test data
    - npm run lint
    - npm run build
    - frontend route/source verification for /recipes, /orders and /orders/:orderId
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m unittest tests.test_cache -v
    - Redis cache key/TTL/invalidation inspection for recipe-order:v1 namespace
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m unittest discover -s tests -p 'test_*.py' -v
    - UV_CACHE_DIR=/tmp/fuye-uv-cache uv run python -m compileall -q app tests
    - npm run lint
    - npm run build
    - docker compose config --quiet
    - git diff --check
    - migration design review: init.sql bootstrap boundary, schema_migrations, backup and deployment ordering
    - docker compose config --quiet
    - uv run 临时真实 HTTP API 验证：admin 图片上传、新增、编辑、上下架、删除；user 对新增/修改/删除/上传均为 403；临时数据库记录和 OSS 对象均已清理
    - uv run 临时真实 HTTP API 验证：空分类状态下 admin 新增分类并创建菜谱，user 新增分类为 403；临时数据已清理
    - curl 本地 Vite /admin/recipes 路由和默认图片资源
    - uv run 临时真实 HTTP API 验证：分类、category_id 筛选、8 条分页、详情和 image_url=null；临时用户、分类和 9 条菜谱均已清理
    - curl 本地 Vite /recipes 路由和默认图片资源
    - docker compose config --quiet
    - psql "$DATABASE_URL" schema inspection and role migration checks
    - real TestClient login and require_admin verification with temporary users
    - backend/.venv/bin/python -m unittest discover -s tests -p 'test_categories.py' -v
    - backend/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
    - psql "$DATABASE_URL" recipe_categories schema and constraint checks
    - real TestClient category read/admin CRUD/permission verification with temporary users and category
    - backend/.venv/bin/python -m unittest discover -s tests -p 'test_recipes.py' -v
    - backend/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
    - psql "$DATABASE_URL" recipes schema, constraints, indexes and cleanup checks
    - real TestClient recipe CRUD/visibility/filter/pagination/permission verification with temporary users, category and recipes
    - git diff --check
    - uv lock
    - uv sync --locked
    - uv run python -m compileall -q app tests
    - uv run python -c 'from app.main import app; ... upload route ...'
    - docker compose config --quiet
    - uv run 临时 TestClient：未登录 401、普通用户 403、非图片 415、空文件 400、伪造图片内容 415、超过 5 MB 413
    - uv run 临时真实 OSS PNG 上传、对象存在性检查和删除清理
    - uv run 修正 endpoint 后临时真实 OSS PNG 上传、对象存在性检查、自定义域名访问和删除清理
    - uv run python -m unittest discover -s tests -p 'test_*.py' -v
    - npm run lint
    - npm run build
- api_contracts: |
    GET /api/categories：需要 Bearer Token；user/admin 可用；返回分类数组 [{id, name, created_at}]。
    POST /api/categories：仅 admin；JSON {"name": string, 1..50 字符}；成功返回分类对象；普通用户 403，重复名称 409。
    PUT /api/categories/{category_id}：仅 admin；JSON {"name": string, 1..50 字符}；成功返回分类对象；不存在 404，普通用户 403。
    DELETE /api/categories/{category_id}：仅 admin；成功返回 {"message": "删除成功", "id": number}；不存在 404，普通用户 403。
    GET /api/recipes：需要 Bearer Token；user 只返回 status=active，admin 可查看全部；支持 page、page_size、category_id、status；返回 {items, page, page_size, total}。
    GET /api/recipes/{recipe_id}：需要 Bearer Token；user 不能查看 inactive，admin 可以查看全部；不存在或对 user 不可见时 404。
    POST /api/recipes：仅 admin；JSON 包含 name、description、price、category_id、image_url、status；成功返回菜谱对象；无效价格 422、分类不存在 404、普通用户 403。
    PUT /api/recipes/{recipe_id}：仅 admin；支持部分更新 name、description、price、category_id、image_url、status；不存在 404，普通用户 403。
    DELETE /api/recipes/{recipe_id}：仅 admin；物理删除；不存在 404；未来存在订单外键引用时返回 409；下架应使用 PUT status=inactive。
    POST /api/upload/image：需要 Bearer Token，且必须是 admin；请求为 multipart/form-data，字段 file。
    成功返回 200：{"url": "https://static.myfeiniao.cn/recipes/{uuid}.jpg|png|webp"}。
    未登录返回 401，普通用户返回 403；不支持的 MIME 或内容签名返回 415；空文件返回 400；超过 5 MB 返回 413；OSS 配置不完整返回 503；OSS 服务拒绝或上传失败返回 502。
    AccessKey 只由后端读取，前端不接触；菜谱未上传图片时继续使用 image_url=null 和前端默认图片路径。
    Phase 5 前端消费接口：GET /api/categories、GET /api/recipes?page&page_size&category_id、GET /api/recipes/{id}，均使用现有 Bearer Token 请求拦截器；401 保持现有行为并跳转登录页。
    Phase 6 前端消费接口：POST /api/recipes、PUT /api/recipes/{id}、DELETE /api/recipes/{id} 和 POST /api/upload/image；均通过现有 Bearer Token 发送，后端仅接受 admin。图片请求为 multipart/form-data 的 file 字段，客户端仅做预校验，后端 MIME/签名/5 MB 校验仍为最终依据。
- open_issues: |
    Phase 1、Phase 2 和 Phase 3 验证通过。TestClient 输出了 Starlette 关于当前 httpx 兼容层的弃用警告，但不影响测试结果；本次没有为此进行无关依赖升级。
    Phase 4 已通过。Bucket ACL 探测仍返回拒绝，但实际 PutObject、HeadObject、自定义域名 GET 和 DeleteObject 均已成功；说明当前上传链路所需对象权限可用，ACL 管理权限不是本 Phase 必需项。
    TestClient 输出了 Starlette 关于当前 httpx 兼容层的弃用警告，但不影响测试结果；AccessKey 曾在对话中暴露，建议在阿里云控制台立即禁用/轮换，并使用最小权限 RAM 用户重新配置。
    Phase 5 的浏览器截图验证受当前环境无可用浏览器控制器限制；已完成真实 API、Vite 路由/静态资源、TypeScript 构建与 lint 验证。
    Phase 6 同样受当前环境无可用浏览器控制器限制，未执行截图级交互验证；已完成真实管理员和普通用户 API、OSS、Vite 路由、TypeScript 构建与 lint 验证。
    Phase 7 测试输出了 Starlette 关于当前 httpx 兼容层的弃用警告，但不影响结果；未进行无关依赖升级。
    Phase 8 测试同样输出 Starlette 关于当前 httpx 兼容层的弃用警告，但不影响结果；未进行无关依赖升级。
    Phase 7 前端补齐后完整后端回归和前端 lint/build 已通过；当前环境无可用浏览器控制器，因此未进行截图级交互验证。
    Phase 9 Redis 不可用时采用回源数据库策略；缓存异常只记录 warning，不影响接口可用性。TestClient 仍有 Starlette/httpx 兼容层弃用警告，未进行无关依赖升级。
    线上数据库迁移仍是 Phase 10 的未完成事项：当前尚未创建 migration runner 或执行任何生产迁移；init.sql 不会自动升级已有数据卷。
- validation_result: passed
- next_step: 用户明确要求继续后，重新读取 GitHub Actions、Dockerfile、Nginx、Compose、环境变量示例和前后端构建脚本，只执行 Phase 10：CI/CD 和部署兼容性最终验证；完成后才可将项目标记 complete。
