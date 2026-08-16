FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

ENV PROBUILD_ENV=production
ENV PROBUILD_API_HOST=0.0.0.0
ENV PROBUILD_API_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "probuild.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
