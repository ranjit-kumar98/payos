FROM node:18-alpine

WORKDIR /app

COPY ./src /app/src
COPY ./package.json /app/package.json
COPY ./package-lock.json /app/package-lock.json

RUN npm install

EXPOSE 3001

CMD ["npm", "start"]