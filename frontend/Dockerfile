# syntax=docker/dockerfile:1

FROM node:20-slim AS base

WORKDIR /app

# Install dependencies first for better layer caching.
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code.
COPY . .

EXPOSE 3000

# Dev mode — hot reload works via polling inside Docker.
ENV WATCHPACK_POLLING=true
CMD ["npm", "run", "dev"]
