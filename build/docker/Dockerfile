# Base
ARG PYTHON_BASE_IMAGE=python:3.11-slim
FROM ${PYTHON_BASE_IMAGE} AS base

# Builder
FROM base AS builder

ARG PIP_FILE=requirements_py3
COPY ./${PIP_FILE}.txt requirements.txt

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends build-essential libffi-dev \
  && pip install --no-cache-dir --disable-pip-version-check --no-warn-script-location --user -r requirements.txt

# App
FROM base

ARG USER=dictrack

ENV HOME=/home/${USER}
ENV PATH=${HOME}/.local/bin:${PATH}

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends htop \
  && useradd -s /bin/bash -m -d ${HOME} ${USER} \
  && mkdir ${HOME}/app \
  && chown -R ${USER}:${USER} ${HOME}/app

RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime && \
  echo "Asia/Taipei" > /etc/timezone

ENV TZ=Asia/Taipei

# WORKDIR ${HOME}/app
WORKDIR /app

USER ${USER}

COPY --chown=${USER}:${USER} --from=builder /root/.local ${HOME}/.local
COPY --chown=${USER}:${USER} ./tmp/app ${HOME}/app

CMD ["tail", "-f", "/dev/null"]
# CMD ["sh", "start.sh"]