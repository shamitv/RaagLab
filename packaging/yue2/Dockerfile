FROM python:3.12-slim-bookworm@sha256:9c47360a2a0355e2da18516d0b1c2126ec22c195d2185e97347c9d98398c5bef
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/weights/cache HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HUB_DISABLE_IMPLICIT_TOKEN=1 TOKENIZERS_PARALLELISM=false
WORKDIR /opt/yue2-test
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir --require-hashes \
    --extra-index-url https://download.pytorch.org/whl/cu128 -r requirements.lock \
    && python -m pip check
COPY model-lock.json acquire.py ./
COPY prompts.json preflight.py generate.py validate.py run.py test_harness.py ./
CMD ["python", "acquire.py"]
