FROM python:3.6-slim

RUN pip install alpaca-trade-api==0.50.1 \
                websockets==8.1

WORKDIR /opt/project

COPY . /opt/project/

CMD python main.py

# Set some environment variables.
# PYTHONUNBUFFERED keeps Python from buffering our standard output stream,
# which means that logs can be delivered to the user quickly.
# PYTHONDONTWRITEBYTECODE keeps Python from writing the .pyc files which are
# unnecessary in this case. We also update

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE



