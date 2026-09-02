FROM node:22-alpine AS dashboard-build
WORKDIR /dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY dashboard ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends nginx apache2-utils && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY --from=dashboard-build /dashboard/dist /usr/share/nginx/html
COPY deploy/render-nginx.conf /etc/nginx/sites-enabled/default
COPY deploy/render-start.sh /app/render-start.sh
RUN chmod +x /app/render-start.sh
EXPOSE 10000
CMD ["/app/render-start.sh"]
