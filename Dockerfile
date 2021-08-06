FROM python:3.8-slim

WORKDIR /opt/project

COPY . /opt/project/
RUN pip install -r requirements.txt

CMD python main.py

# Set some environment variables.
# PYTHONUNBUFFERED keeps Python from buffering our standard output stream,
# which means that logs can be delivered to the user quickly.
# PYTHONDONTWRITEBYTECODE keeps Python from writing the .pyc files which are
# unnecessary in this case. We also update

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE



