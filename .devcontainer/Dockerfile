FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install Python 2.7 and Python 3
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    python2 \
    python2-dev \
    python3 \
    python3-dev \
    python3-pip \
    curl \
    build-essential \
    libffi-dev \
    git \
    sudo

# Install pip for Python 2.7
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py \
    && python2 get-pip.py \
    && rm get-pip.py

# Install common Python tools
RUN python3 -m pip install --upgrade pip setuptools wheel tox virtualenv
RUN python2 -m pip install --upgrade pip setuptools wheel virtualenv

# Clean up
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*
