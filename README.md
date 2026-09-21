# docker-examples

> 可直接用的 Dockerfile 与 docker-compose 示例。

## 文件
- [Dockerfile](Dockerfile)：一个最小的 Python (Flask) 应用镜像
- [docker-compose.yml](docker-compose.yml)：Web + Redis 小栈

## 用法
    docker build -t demo-web .
    docker run -p 5000:5000 demo-web
    # 或
    docker compose up --build

## 生态联动
- CLI 速查（含 docker 篇）→ [@c991china/cli-cheatsheets](https://github.com/c991china/cli-cheatsheets)
- YAML 配置样例 → [@22178384/yaml-configs](https://github.com/22178384/yaml-configs)
