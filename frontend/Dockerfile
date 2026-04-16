FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM alpine:3.19
COPY --from=build /app/dist /app/dist
# Keep the container alive just long enough for the volume to be populated
CMD ["sh", "-c", "echo 'Frontend build complete' && sleep infinity"]
