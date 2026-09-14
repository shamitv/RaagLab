FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/weights/cache \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HUB_DISABLE_IMPLICIT_TOKEN=1 \
    TOKENIZERS_PARALLELISM=false \
    CUDA_VISIBLE_DEVICES=""

WORKDIR /opt/yue2-cpu

ARG YUE_SOURCE_REF=0edaf2f4053ef4731334b8329834b107977f9637

RUN apt-get update \
    && apt-get install --no-install-recommends -y git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.10.0

RUN git clone --depth 1 https://github.com/multimodal-art-projection/YuE.git /opt/YuE \
    && cd /opt/YuE \
    && git fetch --depth 1 origin ${YUE_SOURCE_REF} \
    && git checkout ${YUE_SOURCE_REF} \
    && python -m pip install --no-cache-dir \
         transformers==4.57.6 \
         huggingface-hub==0.36.2 \
         safetensors==0.7.0 \
         tiktoken==0.12.0 \
         numpy==2.2.6 \
         soundfile==0.13.1 \
         accelerate==1.13.0 \
    && python -m pip install --no-cache-dir --no-deps /opt/YuE \
    && python -c "import torch, yue2; assert torch.version.cuda is None; print(torch.__version__, yue2.__version__)"

COPY packaging/yue2/model-lock.json packaging/yue2/acquire.py ./
COPY packaging/yue2-cpu/smoke.py ./

CMD ["python", "smoke.py"]
