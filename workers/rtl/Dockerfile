FROM ghcr.io/ucb-bar/chia:latest

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        jq \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------------------
# Python dependencies
# Existing RTL worker + new UVM generation pipeline.
# --------------------------------------------------------------------
RUN pip install --no-cache-dir \
        jinja2 \
        pyyaml \
        pydantic

# --------------------------------------------------------------------
# Verible
# Existing RTL parsing capability — unchanged.
# --------------------------------------------------------------------
RUN LATEST_TAG=$(curl -fsSL https://api.github.com/repos/chipsalliance/verible/releases/latest | jq -r .tag_name) && \
    echo "Installing Verible ${LATEST_TAG}" && \
    curl -fsSL \
        "https://github.com/chipsalliance/verible/releases/download/${LATEST_TAG}/verible-${LATEST_TAG}-linux-static-x86_64.tar.gz" \
        -o /tmp/verible.tar.gz && \
    mkdir -p /opt/verible && \
    tar -xzf /tmp/verible.tar.gz \
        -C /opt/verible \
        --strip-components=1 && \
    chmod -R a+rX /opt/verible && \
    ln -s /opt/verible/bin/* /usr/local/bin/ && \
    rm /tmp/verible.tar.gz

# --------------------------------------------------------------------
# Existing RTL worker implementation
# --------------------------------------------------------------------
RUN mkdir -p /opt/rtl-worker

COPY workers/rtl/entrypoint.py \
     /opt/rtl-worker/entrypoint.py

COPY workers/rtl/extract_concise.py \
     /opt/rtl-worker/extract_concise.py

RUN chmod -R a+rX /opt/rtl-worker

# --------------------------------------------------------------------
# UVM environment generator
# --------------------------------------------------------------------
RUN mkdir -p /opt/uvm-generator

COPY src/ \
     /opt/uvm-generator/src/

COPY uvm_generator/ \
     /opt/uvm-generator/uvm_generator/

COPY templates/ \
     /opt/uvm-generator/templates/

COPY config/ \
     /opt/uvm-generator/config/

COPY scripts/ \
     /opt/uvm-generator/scripts/

RUN chmod -R a+rX /opt/uvm-generator

# Make the UVM generator importable from anywhere in the container.
ENV PYTHONPATH="/opt/uvm-generator"

USER ray

WORKDIR /home/ray