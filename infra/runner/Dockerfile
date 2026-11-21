# 课程运行器镜像：作业 1 的 DSH-Lens、作业 2/5 的小题都在这个镜像里运行，agent 执行的命令都关在容器内。
# 构建（需要正常网络，只需构建一次）：docker build -t agentharness-runner:0.1 infra/runner
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -i "$PIP_INDEX_URL" deepseek-harness-sdk==0.2.2rc2 zstandard==0.25.0 fastapi==0.165.0 uvicorn==0.54.0
ENV AH_IN_CONTAINER=1 PYTHONUNBUFFERED=1
WORKDIR /work
