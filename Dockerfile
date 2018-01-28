FROM python:3.6.4

RUN pip install \
  pytest==3.3.2

COPY ./* /opt/secretary/

RUN pip install -e /opt/secretary
