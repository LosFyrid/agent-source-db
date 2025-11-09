# AgentCard 备份策略文档

本文档详细说明 AgentCard 系统的完整备份策略，确保数据安全和可恢复性。

---

## 📋 备份目标

### 需要备份的内容

| 内容 | 备份方式 | 频率 | 重要性 |
|------|----------|------|--------|
| **代码** | Git 仓库 | 实时 | ⭐⭐⭐ |
| **生产数据库** | PostgreSQL 导出 | 每天 | ⭐⭐⭐⭐⭐ |
| **测试数据库** | PostgreSQL 导出 | 每周 | ⭐⭐ |
| **配置文件** | 手动备份 | 首次部署后 | ⭐⭐⭐⭐ |
| **上传文件** | Docker Volume | 自动持久化 | ⭐⭐⭐ |

### 不需要备份的内容

- ❌ 静态文件（可通过 `collectstatic` 重新生成）
- ❌ Docker 镜像（可通过 Dockerfile 重新构建）
- ❌ 日志文件（临时数据）

---

## 🔄 备份策略

### 1. 代码备份（Git）

**状态**: ✅ 已自动化

代码通过 Git 版本控制，推送到 GitHub 后自动备份。

```bash
# 查看远程仓库
git remote -v

# 推送代码
git push origin main
```

**恢复方法**:
```bash
git clone https://github.com/YOUR_USERNAME/agent-source-db.git
```

---

### 2. 数据库备份（核心）

#### 2.1 手动备份

```bash
# 备份生产环境
./scripts/backup_database.sh prod

# 备份测试环境
./scripts/backup_database.sh test
```

**备份位置**:
- 生产环境: `backups/prod/backup_prod_YYYYMMDD_HHMMSS.sql.gz`
- 测试环境: `backups/test/backup_test_YYYYMMDD_HHMMSS.sql.gz`

#### 2.2 自动备份（推荐）

**方法 1: 使用交互式配置脚本（最简单）**

```bash
./scripts/setup_cron.sh
```

按提示选择：
1. 备份频率（推荐：每天凌晨 3 点）
2. 备份环境（推荐：仅生产环境）

脚本会自动配置 crontab。

**方法 2: 手动配置 crontab**

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 3 点备份生产环境）
0 3 * * * /home/your_username/projects/agent-source-db/scripts/backup_database.sh prod >> /home/your_username/projects/agent-source-db/logs/backup.log 2>&1
```

**验证 Cron 任务**:

```bash
# 查看当前 crontab
crontab -l

# 查看备份日志
tail -f ~/projects/agent-source-db/logs/backup.log

# 检查 cron 服务状态
systemctl status cron
# 或
systemctl status crond
```

#### 2.3 备份保留策略

- **本地备份**: 自动保留最近 7 个备份
- **手动清理**: 不需要，脚本自动清理旧备份

#### 2.4 数据库恢复

**从备份恢复生产数据库**:

```bash
# 1. 解压备份文件
gunzip backups/prod/backup_prod_20250109_030000.sql.gz

# 2. 恢复到数据库
cat backups/prod/backup_prod_20250109_030000.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U produser agentcard_prod

# 3. 验证数据
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from documents.models import AgentCard
>>> AgentCard.objects.count()
```

**从备份恢复到测试环境**:

```bash
# 使用脚本（推荐）
./scripts/copy_prod_to_test.sh

# 或手动恢复
cat backups/prod/backup_prod_20250109_030000.sql | docker-compose -f docker-compose.test.yml exec -T db psql -U testuser agentcard_test
```

---

### 3. 配置文件备份

**需要手动备份的文件**:

```bash
# 在首次部署后，将这些文件备份到安全位置
.env.prod      # 生产环境配置（包含密码）
.env.test      # 测试环境配置
```

**⚠️ 重要**: 这些文件包含敏感信息（密码、密钥），**不要上传到 Git**！

**推荐备份方法**:

1. **加密备份到本地**:
```bash
# 使用 GPG 加密
tar czf - .env.prod .env.test | gpg -c > env_backup_$(date +%Y%m%d).tar.gz.gpg

# 解密恢复
gpg -d env_backup_20250109.tar.gz.gpg | tar xzf -
```

2. **存储在密码管理器**:
   - 将 `.env.prod` 内容复制到 1Password / Bitwarden 等
   - 标注为 "AgentCard 生产环境配置"

---

## �� 推荐备份计划

### 生产环境

| 任务 | 频率 | 时间 | 保留期 |
|------|------|------|--------|
| 数据库备份 | 每天 | 凌晨 3:00 | 7 天 |
| 配置文件备份 | 首次部署 + 每次修改后 | 手动 | 永久 |

**Crontab 配置**:
```bash
# 每天凌晨 3 点备份生产数据库
0 3 * * * /path/to/agent-source-db/scripts/backup_database.sh prod >> /path/to/agent-source-db/logs/backup.log 2>&1
```

### 测试环境

| 任务 | 频率 | 时间 | 保留期 |
|------|------|------|--------|
| 数据库备份 | 每周 | 周日凌晨 2:00 | 4 个 |

**Crontab 配置**:
```bash
# 每周日凌晨 2 点备份测试数据库
0 2 * * 0 /path/to/agent-source-db/scripts/backup_database.sh test >> /path/to/agent-source-db/logs/backup.log 2>&1
```

---

## 🧪 备份验证

### 定期验证备份可用性

**每月至少验证一次**备份是否可以成功恢复：

```bash
# 1. 创建临时测试容器
docker run -d --name test-restore -e POSTGRES_PASSWORD=testpass postgres:18-alpine

# 2. 恢复备份到测试容器
gunzip -c backups/prod/backup_prod_20250109_030000.sql.gz | docker exec -i test-restore psql -U postgres

# 3. 验证数据
docker exec -it test-restore psql -U postgres -c "SELECT COUNT(*) FROM agent_cards;"

# 4. 清理测试容器
docker rm -f test-restore
```

---

## 🚨 灾难恢复场景

### 场景 1: 数据库数据丢失

**症状**: AgentCard 数据全部丢失

**恢复步骤**:
```bash
# 1. 找到最新备份
ls -lt backups/prod/

# 2. 恢复备份
gunzip backups/prod/backup_prod_20250109_030000.sql.gz
cat backups/prod/backup_prod_20250109_030000.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U produser agentcard_prod

# 3. 重启服务
docker-compose -f docker-compose.prod.yml restart web

# 4. 验证数据
curl http://YOUR_SERVER_IP:8000/api/agentcards/
```

**数据损失**: 最多 24 小时（自上次备份以来）

---

### 场景 2: 服务器完全崩溃

**症状**: 服务器硬件故障，无法启动

**恢复步骤**:
```bash
# 在新服务器上

# 1. 安装 Docker 和 Git
sudo apt update && sudo apt install -y docker.io docker-compose git

# 2. 克隆代码
git clone https://github.com/YOUR_USERNAME/agent-source-db.git
cd agent-source-db

# 3. 恢复配置文件（从密码管理器或加密备份）
nano .env.prod  # 粘贴保存的配置

# 4. 启动服务
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 5. 恢复数据库（从异地备份或本地副本）
cat backup_prod_20250109_030000.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U produser agentcard_prod

# 6. 收集静态文件
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 7. 创建管理员账号（如果需要）
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

**恢复时间**: 约 30-60 分钟

---

### 场景 3: 误删除数据

**症状**: 众包团队不小心删除了重要的 AgentCard

**恢复步骤**:
```bash
# 1. 立即停止服务（防止更多操作）
docker-compose -f docker-compose.prod.yml stop web

# 2. 从最近的备份恢复（临时数据库）
docker run -d --name temp-restore -e POSTGRES_PASSWORD=temppass postgres:18-alpine
gunzip -c backups/prod/backup_prod_20250109_030000.sql.gz | docker exec -i temp-restore psql -U postgres

# 3. 导出被删除的数据
docker exec temp-restore psql -U postgres -c "COPY (SELECT * FROM agent_cards WHERE name='DELETED_CARD') TO STDOUT WITH CSV HEADER;" > deleted_card.csv

# 4. 重新导入到生产环境
# （需要根据实际情况编写导入脚本）

# 5. 清理临时容器
docker rm -f temp-restore

# 6. 重启生产服务
docker-compose -f docker-compose.prod.yml start web
```

---

## ✅ 检查清单

博后应该定期（每月）检查：

- [ ] Cron 任务正常运行（`crontab -l`）
- [ ] 备份文件正常生成（`ls -lh backups/prod/`）
- [ ] 备份日志无错误（`tail -f logs/backup.log`）
- [ ] 备份文件大小合理（不是 0 字节）
- [ ] 配置文件已安全保存（密码管理器或加密备份）
- [ ] 至少验证一次备份恢复（测试恢复流程）

---

## 📚 参考命令

```bash
# 查看所有备份文件
find backups/ -name "*.sql.gz" -ls

# 检查备份文件大小
du -sh backups/prod/*

# 查看最新 5 个备份
ls -lt backups/prod/ | head -6

# 验证压缩文件完整性
gunzip -t backups/prod/backup_prod_20250109_030000.sql.gz

# 查看备份日志
tail -100 logs/backup.log

# 手动触发备份（测试）
./scripts/backup_database.sh prod
```

---

## ⚠️ 注意事项

1. **永远不要删除所有备份** - 至少保留一个可用备份
2. **���期验证备份** - 不验证的备份等于没有备份
3. **保护配置文件** - `.env.prod` 泄露等于密码泄露
4. **监控磁盘空间** - 备份会占用磁盘空间
5. **记录恢复流程** - 在压力下很容易忘记步骤

---

**备份是保险，不是负担。定期备份，安心工作。**
