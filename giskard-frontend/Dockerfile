# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:lts as build-stage

WORKDIR /app

COPY package*.json /app/

RUN apt-get update -y && apt-get install -y libxml2-dev libgcrypt-dev
RUN npm install

COPY ./ /app/

ARG FRONTEND_ENV=production

ENV VUE_APP_ENV=${FRONTEND_ENV}

# Comment out the next line to disable tests
#RUN npm run test:unit

RUN npm run build


# Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
FROM nginx:alpine

COPY --from=build-stage /app/dist/ /usr/share/nginx/html
COPY packaging/nginx.conf /etc/nginx/conf.d/default.conf
