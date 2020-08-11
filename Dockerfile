FROM python:3.6-slim

RUN pip install alpaca-trade-api==0.49.1 \
                websockets==8.1 \
                websocket-client==0.57.0

WORKDIR /opt/project

COPY requirements.txt ./

# Set some environment variables.
# PYTHONUNBUFFERED keeps Python from buffering our standard output stream,
# which means that logs can be delivered to the user quickly.
# PYTHONDONTWRITEBYTECODE keeps Python from writing the .pyc files which are
# unnecessary in this case. We also update

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE



