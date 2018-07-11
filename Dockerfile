FROM python:3.5-alpine

WORKDIR /usr/src/app
#ENV PYTHONPATH /usr/src/app/corp_hq_users

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY setup.py .
COPY corp_hq_auto_scale/ ./corp_hq_auto_scale/
RUN pip install -e .
ENTRYPOINT ["corp-hq-auto-scale"]