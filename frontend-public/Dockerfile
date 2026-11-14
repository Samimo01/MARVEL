# ==========================================
# Etape 1 : Construction de l'application
# ==========================================
FROM node:22-alpine AS builder

WORKDIR /app

# Copie des fichiers de dependances
COPY package*.json ./

# Installation reproductible des dependances
RUN npm ci

# Copie du code source
COPY . .

# URL de l'API (vide = appels relatifs /api)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

# Compilation de l'application React / Vite
RUN npm run build

# ==========================================
# Etape 2 : Serveur web Nginx
# ==========================================
FROM nginx:alpine AS production

# Suppression de la configuration Nginx par defaut
RUN rm /etc/nginx/conf.d/default.conf

# Copie de notre configuration Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copie des fichiers compiles
COPY --from=builder /app/dist /usr/share/nginx/html

# Port HTTP
EXPOSE 80

# Demarrage de Nginx
CMD ["nginx", "-g", "daemon off;"]
