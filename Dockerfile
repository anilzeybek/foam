FROM ubuntu:24.04

LABEL maintainer="Sai Coumar <sai.c.coumar1@gmail.com>"

# Environment variables
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
ENV XDG_RUNTIME_DIR=/tmp/runtime-docker
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all
ENV TERM=xterm-256color
ENV PATH="/home/user/bin:${PATH}"

# Set default shell during Docker image build to bash
SHELL ["/bin/bash", "-l", "-c"]

# Update system and install required dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libprotobuf-dev \
    protobuf-compiler \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set ARG for GitHub token
ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

RUN --mount=type=secret,id=github_token \
    GITHUB_TOKEN=$(cat /run/secrets/github_token) && \
    git config --global url."https://${GITHUB_TOKEN}@github.com".insteadOf "https://github.com" && \
    git clone https://github.com/CoMMALab/foam && \
    cd foam && \
    # Modify submodule URLs to use HTTPS instead of SSH
    sed -i 's|git@github.com:|https://${GITHUB_TOKEN}@github.com/|g' .gitmodules && \
    git submodule update --init --recursive


# Set the default working directory
WORKDIR /foam

# Run the build process
RUN cmake -Bbuild -GNinja . && \
    cmake --build build/

# Default command
CMD ["bash"]
