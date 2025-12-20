FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 4200

ENV NG_CLI_ANALYTICS="false"

CMD ["npm","run", "easy-prod"]
