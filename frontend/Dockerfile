FROM node:18-alpine

WORKDIR /app

COPY ./src /app/src
COPY ./public /app/public
COPY ./package.json /app/package.json
COPY ./package-lock.json /app/package-lock.json

RUN npm install

EXPOSE 3000

CMD ["npm", "start"]