# ==========================================
# Etape 1 : Construction de l'application
# ==========================================
FROM node:22-alpine AS builder

WORKDIR /app

# Installation reproductible des dependances
COPY package*.json ./
RUN npm ci

# Copie du code source
COPY . .

# Compilation React / TypeScript / Vite
RUN npm run build

# ==========================================
# Etape 2 : Serveur web Nginx
# ==========================================
FROM nginx:alpine AS production

# Suppression de la configuration Nginx par defaut
RUN rm /etc/nginx/conf.d/default.conf

# Configuration personnalisee
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Fichiers compiles
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
