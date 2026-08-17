FROM node:18-alpine

WORKDIR /app

COPY ./src /app/src
COPY ./public /app/public
COPY ./package.json /app/package.json
COPY ./package-lock.json /app/package-lock.json
COPY ./vite.config.js /app/vite.config.js
COPY ./index.html /app/index.html

RUN npm install

EXPOSE 3000

CMD ["npm", "run", "dev"]
