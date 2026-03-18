# ==========================================
# Dockerfile para Frontend (React)
# ==========================================

# Etapa 1: Construir la aplicación
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar package.json primero (para cache)
COPY package.json yarn.lock ./

# Instalar dependencias
RUN yarn install --frozen-lockfile

# Copiar código fuente
COPY . .

# Construir la aplicación
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN yarn build

# Etapa 2: Servir con nginx
FROM nginx:alpine

# Copiar build
COPY --from=builder /app/build /usr/share/nginx/html

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
