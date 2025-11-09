# 运维脚本说明

本目录包含 AgentCard 系统的运维脚本，简化博后的日常操作。

## 脚本列表

### 1. deploy.sh - 快速部署/更新

**功能**: 一键部署或更新环境（拉取代码 → 构建 → 启动 → 迁移 → 收集静态文件）

**使用方法**:
```bash
# 部署/更新测试环境
./scripts/deploy.sh test

# 部署/更新生产环境
./scripts/deploy.sh prod
```

**适用场景**:
- 首次部署
- 代码更新后重新部署
- 数据库 Schema 变更后迁移

---

### 2. backup_database.sh - 数据库备份

**功能**: 备份数据库并压缩，自动清理旧备份（保留最近7个）

**使用方法**:
```bash
# 备份生产数据库
./scripts/backup_database.sh prod

# 备份测试数据库
./scripts/backup_database.sh test
```

**备份位置**:
- 生产环境: `backups/prod/backup_prod_YYYYMMDD_HHMMSS.sql.gz`
- 测试环境: `backups/test/backup_test_YYYYMMDD_HHMMSS.sql.gz`

---

### 2.1 setup_cron.sh - 配置自动备份（推荐使用）

**功能**: 交互式配置 crontab 自动备份任务

**使用方法**:
```bash
./scripts/setup_cron.sh
```

**交互流程**:
1. 选择备份频率（每天凌晨 3 点/每周日凌晨 2 点/自定义）
2. 选择备份环境（仅生产/仅测试/两者）
3. 自动配置 crontab 并验证

**示例**:
```
请选择备份频率:
1) 每天凌晨 3 点（推荐）
2) 每周日凌晨 2 点

请输入选项: 1

请选择备份环境:
1) 仅生产环境（推荐）

请输入选项: 1

✓ Cron 任务已添加！
```

**验证配置**:
```bash
# 查看 crontab
crontab -l

# 查看备份日志
tail -f logs/backup.log
```

---

### 3. copy_prod_to_test.sh - 复制生产数据到测试环境

**功能**: 将生产环境的真实数据复制到测试环境

**使用方法**:
```bash
./scripts/copy_prod_to_test.sh
```

**适用场景**:
- 测试环境需要真实数据进行验证
- 验证数据库迁移是否会影响现有数据
- 在测试环境复现生产问题

**警告**: 会覆盖测试环境的所有数据，操作前会提示确认

---

## 常见操作流程

### 场景 1: 开发者提交了新功能，需要部署

```bash
# 1. 先部署到测试环境验证
./scripts/deploy.sh test

# 2. 访问测试环境检查功能
http://YOUR_SERVER_IP:8001/admin/

# 3. 验证通过后，部署到生产环境
./scripts/deploy.sh prod
```

### 场景 2: 设置自动备份（首次部署后必做）

```bash
# 使用交互式配置脚本（推荐）
./scripts/setup_cron.sh

# 或手动备份
./scripts/backup_database.sh prod
```

### 场景 3: 测试环境需要生产数据

```bash
# 复制生产数据到测试环境
./scripts/copy_prod_to_test.sh
```

---

## 手动操作参考

如果脚本无法使用，可以使用以下手动命令：

### 启动服务
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 查看日志
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### 重启服务
```bash
docker-compose -f docker-compose.prod.yml restart
```

### 停止服务
```bash
docker-compose -f docker-compose.prod.yml stop
```

### 数据库迁移
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 创建管理员
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

