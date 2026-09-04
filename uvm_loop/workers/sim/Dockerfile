FROM ubuntu:24.04

ARG VERILATOR_VERSION=5.042
ARG UVM_VERSION=1800.2-2020.3.1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget git autoconf flex bison help2man perl \
    python3 python3-dev g++ make libfl-dev z3 python3-yaml \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch v${VERILATOR_VERSION} \
        https://github.com/verilator/verilator.git /tmp/verilator \
    && cd /tmp/verilator \
    && autoconf \
    && ./configure \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/verilator

RUN wget -q \
        https://www.accellera.org/images/downloads/standards/uvm/UVM-${UVM_VERSION}.tar.gz \
        -O /tmp/uvm.tar.gz \
    && mkdir -p /opt/uvm \
    && tar -xzf /tmp/uvm.tar.gz -C /opt/uvm --strip-components=1 \
    && rm /tmp/uvm.tar.gz

ENV UVM_HOME=/opt/uvm/src
ENV PATH="/usr/local/bin:${PATH}"

COPY workers/sim/run.py /workspace/workers/sim/run.py

ENTRYPOINT ["python3", "/workspace/workers/sim/run.py"]
