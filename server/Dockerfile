FROM python:3.10.5-slim-buster

ARG MODE
ARG APP_HOME

RUN apt-get update && \
    apt-get install --no-install-recommends -y libpq-dev build-essential libgl1-mesa-glx libglib2.0-0 python3-opencv ffmpeg && \
    apt-get clean

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

COPY . ${APP_HOME}
WORKDIR ${APP_HOME}

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install ${MODE} --no-interaction --no-ansi --no-root
