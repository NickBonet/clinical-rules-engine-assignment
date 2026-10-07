# Frontend image: build the Vite bundle, then serve it with nginx.
FROM node:24-alpine AS build

WORKDIR /app

# Use the public npm registry for container builds.
COPY package.json package-lock.json .npmrc ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.31-alpine

# Configure API proxying and frontend routes.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
