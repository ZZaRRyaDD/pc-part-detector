# Frontend
FROM node:lts-alpine as build-stage

WORKDIR /app

COPY ./frontend/package*.json ./
COPY ./frontend/ .

RUN npm install
RUN npm run build

# Nginx
FROM nginx:stable-alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./nginx/default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
