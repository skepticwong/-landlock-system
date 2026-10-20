FROM node:12

WORKDIR /app
COPY package*jsopn ./
RUN NPM INSTALL 
COPY . .

ENV PORT=5000

EXPOSE 5000

CMD ["npm","start"]