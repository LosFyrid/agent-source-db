# 项目文档：结构化文档管理 API 与后台

## 1. 项目概览

本项目旨在构建一个**健壮的、可扩展的文档管理系统**。

核心功能是提供一个**内部管理后台**（用于“众包式、零散地”录入和管理结构化文档）和一个**高性能的 API 层**（用于将这些文档暴露给生产环境的服务）。

该系统从零开始设计，充分考虑了多环境部署（开发、测试、生产）、可维护性、安全性和未来可扩展性（例如，集成 LLM 进行数据提取）。

---

## 2. 核心架构

本系统采用**“演进中的单体 (Evolving Monolith)”**架构。

* **原始方案：** `Web (Django)` + `DB (PostgreSQL)`。这是一个紧密耦合的单体应用，`Django` 同时负责 API 和管理后台。
* **架构选型：** 这**不是**一个微服务架构。它是一个务实的选择，`Django` 作为核心服务，管理着共享的 `PostgreSQL` 数据库。
* **未来扩展：** 该架构为“面向服务的架构 (SOA)”预留了空间。未来可以通过添加 `Redis` 和 `Celery Worker` 服务，将“慢任务”（如 LLM 提取）从主 Web 服务中异步剥离，而无需重构整个系统。

---

## 3. 技术选型 (Tech Stack)

每一个技术选择都基于“**稳定性、开发速度、社区支持和最佳实践**”的权衡。

| 类别 | 选择 | 镜像/版本 | 为什么选择它？ |
| :--- | :--- | :--- | :--- |
| **后端框架** | **Django** | N/A | **核心选择。** Django 的“杀手级功能”是 `django-admin`，它**自动生成**一个功能齐全、安全的管理后台，完美满足“众包录入”需求，节省数周的前端开发。 |
| **API** | **Django Rest Framework (DRF)** | N/A | Django 生态的“黄金标准”，可极快地将数据模型（Models）转换为安全、可浏览的 REST API。 |
| **数据库** | **PostgreSQL** | `postgres:18-alpine` | `18` 是当前最新稳定版，功能先进。`alpine` 镜最小，资源占用低。**为什么不用 SQLite？** PostgreSQL 是生产级服务器，支持高并发读写，而 SQLite 只是一个文件，有并发锁问题。 |
| **Python** | **Python** | `python:3.11-slim` | **为什么 3.11？** “黄金版本”，性能（比 3.10 快）和生态（所有依赖都已完美支持）的最佳平衡点。**为什么不用 3.13？** 太新，生态（如 `psycopg2`）的预编译轮子（wheels）可能不全，会导致“依赖地狱”。 |
| | **(镜像标签)** | `-slim` | **为什么不用 `-alpine`？** Python 生态严重依赖 C 扩展。`alpine` 使用 `musl` C 库，而 `slim` (Debian) 使用 `glibc`。几乎所有预编译轮子都是为 `glibc` 构建的。使用 `slim` 能避免在 Docker 中从源码编译，**极大**缩短构建时间。 |
| **Web 服务器** | **Gunicorn** | N/A | **为什么不用 uWSGI？** Gunicorn 配置极其简单、纯 Python、可靠。uWSGI 功能强大但配置极其复杂。Gunicorn 是“简单可靠”的最佳选择。 |
| **环境管理** | **Docker** | N/A | **Docker 容器 *就是* 虚拟环境。** 它隔离了整个操作系统（Python 版本、系统库、Python 包），提供了比 `venv` 更彻底、更可复现的环境隔离。 |
| **编排** | **Docker Compose** | N/A | 用于在本地开发中一键启动和管理 `web`、`db` 等多个关联服务。 |

---

## 4. 开发环境：“黄金工作流” (Windows + WSL 2)

本方案专为在 Windows 主机上使用 WSL 2 (Ubuntu) 进行专业 Python 开发而设计。

### 4.1. 理念：“转发”模式

* **为什么不用 WSL 2 装 Docker？** 我们**不**在 WSL 2 (Ubuntu) 内部 `apt install docker`。
* **我们用什么？** 我们使用 **Windows 版的 Docker Desktop**。
* **为什么？** Docker Desktop 是一个“发动机包”，它在后台运行 Docker 引擎，并**必须**启用“WSL 2 Integration”。
* **“转发”的魔力：**
    1.  **网络：** Docker Desktop 自动处理 Windows 和 WSL 2 之间的网络转发。你在 WSL 2 容器里启动的 `localhost:8000`，可以直接在 Windows Chrome 浏览器中访问。
    2.  **服务：** Docker Desktop 随 Windows 启动，解决了 WSL 2 默认没有 `systemd` 导致你必须“手动启动服务”的痛点。
    3.  **GUI 与资源：** 它提供了一个 GUI 来管理资源、清理镜像，并且将 Docker 引擎与你的开发环境（Ubuntu）隔离，更稳定。

### 4.2. 本地工具栈

1.  **主机 OS：** Windows 10/11
2.  **开发环境：** WSL 2 (Ubuntu)
3.  **Docker：** **Docker Desktop for Windows** （启用 WSL 2 Integration）
4.  **编辑器：** **VS Code (Windows 版)**
5.  **VS Code 关键插件：**
    * `Remote - WSL`：**必备。** 让你“连接”进 WSL 2，VS Code 界面在 Win，但所有操作都在 Linux。
    * `Docker`：**必备。** 这是一个 VS Code “前端”，用于连接 Docker Desktop “后端”，让你在 VS Code 侧边栏就能管理容器和日志。

### 4.3. 每日启动流程

1.  从 Windows“开始”菜单启动 `Ubuntu`。
2.  `cd ~/projects/my_project`
3.  输入 `code .`
4.  VS Code (Windows) 启动，并自动“连接”到 WSL 2。
5.  在 VS Code **内置终端**（它现在是 WSL 2 终端）中，运行 `docker-compose up -d`。
6.  开始开发。

---

## 5. 本地开发工作流：“驾驶舱 vs 发动机”

这是理解 Docker 开发**最关键**的概念。

* **驾驶舱 (Cockpit)：** 你的 WSL 2 主机。
    * 你的 VS Code 在这里运行。
    * 你的**源代码**（`.py`, `.yml`）**存储在这里**。
    * 你在这里“编辑”代码。
* **发动机 (Engine)：** `web` Docker 容器。
    * 你的代码**运行在这里**。
    * `django`, `psycopg2` 等所有依赖**安装在这里**。
    * **本地 WSL 2 不需要 `venv`！** 因为容器 *就是* 你的虚拟环境。

### 工作流：

1.  **同步 (Volume Mount)：** `docker-compose.yml` 中的 `volumes: [.:/app]` 建立了一个“实时传送门”。
2.  **编辑 (在驾驶舱)：** 你在 VS Code (WSL 2) 中修改 `models.py` 并保存。
3.  **传送：** `volumes` 立即将你保存的文件同步到 `web` 容器（发动机）的 `/app` 目录。
4.  **执行 (在发动机)：** 你在 VS Code 终端（驾驶舱）输入 `docker-compose exec web python manage.py migrate`。
5.  **遥控：** Docker 将 `migrate` 命令“遥控”发送到 `web` 容器（发动机）内部去执行。

---

## 6. 工程化与最佳实践

我们从一开始就采用“专业级”的工程实践。

### 6.1. 包管理 (uv + pip)

* **`conda` / `venv`：** **不使用。** Docker 容器是我们的环境。
* **`requirements.in`：** **你手动维护。** 这是你的“直接依赖”源文件（如 `django`）。
* **`requirements.txt`：** **自动生成。** 这是一个“锁文件”，包含所有依赖的**确切**版本。
* **`uv`：** **本地工具 (WSL 2)。** 我们用它 `uv pip compile requirements.in -o requirements.txt` 来快速生成锁文件。
* **`pip`：** **容器内工具。** `Dockerfile` 中只使用 `pip install -r requirements.txt` 来进行可复现的构建。

### 6.2. 代码规范 (Ruff + pyproject.toml)

* **`pyproject.toml`：** 现代 Python 项目的“控制中心”。
* **`[tool.ruff]`：** 我们用 Ruff 一个工具，替代 `black`, `flake8`, `isort` 等多个工具。
* **`line-length = 88`：** 遵循 `black` 的默认标准，这是现代 Python 社区的“事实标准”。

### 6.3. 关键配置与“陷阱”

1.  **`.dockerignore`：**
    * **必须有！** 此文件（语法类似 `.gitignore`）告诉 Docker 在 `COPY . .` 时忽略 `.git`, `__pycache__`, `.venv` 等。
    * **效果：** 极大地减小镜像体积，加快构建速度。

2.  **文件权限 (`UID/GID` 修复)：**
    * **问题：** `docker-compose run ...` 时，容器内的 `root` (ID 0) 创建了文件。当 `volumes` 把文件同步回 WSL 2 时，你本地的 `user` (ID 1000) **没有权限**编辑这些“天赐”的 `root` 文件。
    * **解决方案：**
        1.  在 `.env.dev` 中添加 `UID=$(id -u)` 和 `GID=$(id -g)`。
        2.  在 `docker-compose.yml` 的 `web` 服务中添加 `user: "${UID}:${GID}"`。
    * **效果：** 这强制 Docker 容器内的进程**也**以你本地用户 (ID 1000) 的身份运行，从而使两个世界的文件权限**完美同步**。