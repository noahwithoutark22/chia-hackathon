FROM ubuntu:24.04

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        python3 \
        && \
    rm -rf /var/lib/apt/lists/*

# Install OpenCode CLI.
RUN curl -fsSL https://opencode.ai/install | bash

COPY workers/llm/entrypoint.py /opt/llm-worker/entrypoint.py

ENTRYPOINT ["python3", "/opt/llm-worker/entrypoint.py"]