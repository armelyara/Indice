# Indice — container image.
# Works as-is for Hugging Face Spaces (SDK: docker, app_port: 7860).
FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .

# Runtime data in a writable, ephemeral directory (demo). Override with INDICE_DATA.
ENV INDICE_DATA=/tmp/indice
RUN mkdir -p /tmp/indice && chmod 777 /tmp/indice

EXPOSE 7860
CMD ["indice", "serve", "--host", "0.0.0.0", "--port", "7860"]
