FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY nurse.py activity_log.py memory_bridge.py ./
COPY integrations ./integrations
COPY fixtures ./fixtures
COPY docs/fixtures-img/red-actions-permission-failure.png ./docs/fixtures-img/
COPY web ./web
# Optional demo trace path (created empty so health/activity status is stable)
RUN mkdir -p demo/activity
ENV PORT=8787
EXPOSE 8787
CMD ["uvicorn", "nurse:app", "--host", "0.0.0.0", "--port", "8787"]
