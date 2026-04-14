FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh
EXPOSE 8000
RUN adduser --disabled-password --gecos "" appuser
RUN mkdir -p /app/logs && chown appuser:appuser /app/logs
USER appuser
CMD ["./entrypoint.sh"]