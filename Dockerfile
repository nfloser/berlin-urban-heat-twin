FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json ./
COPY frontend/index.html ./
COPY frontend/src ./src
COPY frontend/scripts ./scripts
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY --from=frontend /app/frontend/dist ./frontend/dist
COPY data ./data
ENV HEAT_TWIN_DATA_DIR=/app/data/cache
EXPOSE 8000
CMD ["uvicorn", "berlin_heat_twin.api:app", "--host", "0.0.0.0", "--port", "8000"]
