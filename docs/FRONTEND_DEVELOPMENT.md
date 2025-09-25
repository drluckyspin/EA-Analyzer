# Frontend Development with Hot Reload

This document explains how to set up and use the hot reload development environment for the EA-Analyzer frontend.

## Overview

The EA-Analyzer frontend supports two modes:

- **Production Mode**: Optimized build with static assets
- **Development Mode**: Hot reload with live file watching

## Quick Start

### Development Mode (Recommended for UI work)

```bash
# Start all services in development mode with hot reload (foreground - shows logs)
make run-web-dev

# Start all services in development mode (detached - runs in background)
make run-web-dev-detached

# Stop development services
make stop-web-dev

# View development logs (only needed if using detached mode)
make logs-web-dev
```

### Production Mode

```bash
# Start all services in production mode
make run-web

# Stop production services
make stop-web

# View production logs
make logs-web
```

## How Hot Reload Works

### File Mounting

The development setup mounts your local frontend files into the Docker container:

```yaml
volumes:
  - ./frontend/src:/app/src:ro # Source code
  - ./frontend/public:/app/public:ro # Static assets
  - ./frontend/package.json:/app/package.json:ro
  - ./frontend/next.config.js:/app/next.config.js:ro
  - ./frontend/tailwind.config.ts:/app/tailwind.config.ts:ro
  - ./frontend/tsconfig.json:/app/tsconfig.json:ro
  - ./frontend/postcss.config.js:/app/postcss.config.js:ro
```

### What Gets Hot Reloaded

✅ **Files that trigger hot reload:**

- React components (`*.tsx`, `*.jsx`)
- TypeScript files (`*.ts`, `*.js`)
- CSS files (`*.css`)
- Tailwind configuration changes
- Next.js configuration changes

❌ **Files that require container restart:**

- `package.json` (new dependencies)
- `next.config.js` (major config changes)
- `tailwind.config.ts` (major config changes)

### Development vs Production Differences

| Aspect             | Development Mode           | Production Mode            |
| ------------------ | -------------------------- | -------------------------- |
| **Build**          | Development build          | Optimized production build |
| **Hot Reload**     | ✅ Enabled                 | ❌ Disabled                |
| **File Watching**  | ✅ Live file mounting      | ❌ Static files            |
| **Performance**    | Slower (dev tools)         | Faster (optimized)         |
| **Debugging**      | Full source maps           | Minified code              |
| **Container Name** | `ea-analyzer-frontend-dev` | `ea-analyzer-frontend`     |
| **API URL**        | `http://localhost:8000`    | `http://backend:8000`      |

## Development Workflow

### 1. Start Development Environment

```bash
make run-web-dev
```

This will:

- Build development Docker images
- Start Neo4j, Backend, and Frontend services
- Mount your local files for hot reload
- Enable Next.js development server
- **Run in foreground** - you'll see all logs in real-time
- **Press Ctrl+C** to stop all services

### 2. Make Changes

Edit any file in `frontend/src/` and see changes reflected immediately:

```bash
# Example: Edit a component
vim frontend/src/components/CustomNode.tsx

# Changes appear instantly in browser at http://localhost:3000
```

### 3. View Logs

```bash
# View all development logs
make logs-web-dev

# View only frontend logs
docker logs ea-analyzer-frontend-dev -f
```

### 4. Stop Development

**If running in foreground mode:**

- Press `Ctrl+C` in the terminal where `make run-web-dev` is running

**If running in detached mode:**

```bash
make stop-web-dev
```

## File Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components
│   ├── lib/                 # Utilities and theme
│   └── types/               # TypeScript types
├── public/                  # Static assets
├── Dockerfile              # Production build
├── Dockerfile.dev          # Development build
├── package.json            # Dependencies
├── next.config.js          # Next.js configuration
├── tailwind.config.ts      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── postcss.config.js       # PostCSS configuration
```

## Configuration Files

### Development Dockerfile (`Dockerfile.dev`)

```dockerfile
FROM node:18-alpine

# Install dependencies
RUN apk add --no-cache libc6-compat

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package.json ./

# Install dependencies
RUN npm install

# Copy source code (overridden by volume mounts)
COPY frontend/src ./src
COPY frontend/public ./public
# ... other config files

# Start development server
CMD ["npm", "run", "dev"]
```

### Development Docker Compose (`docker-compose.dev.yml`)

```yaml
services:
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile.dev
    container_name: ea-analyzer-frontend-dev
    environment:
      - NODE_ENV=development
      - WATCHPACK_POLLING=true # Enable file polling
    volumes:
      # Mount source files for hot reload
      - ./frontend/src:/app/src:ro
      # ... other mounts
```

## Troubleshooting

### Hot Reload Not Working

1. **Check file permissions:**

   ```bash
   ls -la frontend/src/
   ```

2. **Verify volume mounts:**

   ```bash
   docker inspect ea-analyzer-frontend-dev | grep -A 10 "Mounts"
   ```

3. **Check Next.js logs:**

   ```bash
   docker logs ea-analyzer-frontend-dev -f
   ```

4. **Restart development environment:**
   ```bash
   make stop-web-dev
   make run-web-dev
   ```

### API Connection Issues

1. **"Failed to fetch" or "ERR_NAME_NOT_RESOLVED" errors:**

   This usually means the frontend can't connect to the backend API. In development mode, the frontend runs in the browser and needs to connect to `http://localhost:8000`, not `http://backend:8000`.

   **Solution:**

   ```bash
   # Restart with correct API URL
   make stop-web-dev
   make run-web-dev
   ```

2. **Check API URL configuration:**

   ```bash
   # Verify the environment variable is set correctly
   docker exec ea-analyzer-frontend-dev env | grep NEXT_PUBLIC_API_URL
   ```

3. **Test backend connectivity:**

   ```bash
   # Test if backend is accessible
   curl http://localhost:8000/health
   ```

### Performance Issues

1. **Enable polling (if file watching fails):**

   ```yaml
   environment:
     - WATCHPACK_POLLING=true
   ```

2. **Check system resources:**
   ```bash
   docker stats ea-analyzer-frontend-dev
   ```

### Container Issues

1. **Clean up containers:**

   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
   docker system prune -f
   ```

2. **Rebuild from scratch:**
   ```bash
   make stop-web-dev
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
   make run-web-dev
   ```

## Best Practices

### 1. File Organization

- Keep components in `frontend/src/components/`
- Use TypeScript for all new files
- Follow the existing theme system in `frontend/src/lib/theme.ts`

### 2. Development Workflow

- Always use `make run-web-dev` for UI development
- Test changes in development mode before switching to production
- Use `make logs-web-dev` to monitor compilation and errors

### 3. Performance

- Development mode is slower than production
- Use production mode for final testing and demos
- Hot reload works best with smaller, focused changes

### 4. Dependencies

- Add new npm packages to `frontend/package.json`
- Restart the development environment after adding dependencies
- Use `npm install` locally to update `package-lock.json`

## Access URLs

When running in development mode:

- **Frontend**: http://localhost:3000 (with hot reload)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

## Next Steps

1. **Start developing**: `make run-web-dev`
2. **Edit components**: Make changes in `frontend/src/components/`
3. **See changes**: Refresh browser or wait for automatic reload
4. **Test thoroughly**: Switch to production mode for final testing

For more information, see the main [README.md](README.md) and [WEB_APP_README.md](WEB_APP_README.md).
