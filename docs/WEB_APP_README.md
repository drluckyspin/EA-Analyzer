# EA Analyzer Web Application

A modern web application for visualizing and analyzing electrical diagrams using React Flow, FastAPI, and Neo4j.

## Architecture

The web application consists of three main components:

- **Frontend**: Next.js application with React Flow for graph visualization
- **Backend**: FastAPI REST API for data access and business logic
- **Database**: Neo4j graph database for storing electrical diagram data

## Features

- **Interactive Graph Visualization**: View electrical diagrams as interactive node-edge graphs
- **Diagram Selection**: Dropdown to select and switch between different diagrams
- **Real-time Data**: Live connection to Neo4j database
- **Responsive Design**: Modern UI built with Tailwind CSS and Shadcn components
- **Custom Node Types**: Color-coded nodes for different electrical components
- **Custom Edge Types**: Different edge styles for different relationship types

## Quick Start

### Using Docker Compose (Recommended)

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Neo4j Browser: http://localhost:7474

3. **Load some data** (if not already loaded):
   ```bash
   # Use the CLI to analyze and store a diagram
   ./ea-analyzer-cli.sh analyze substation.png --store
   ```

### Manual Development Setup

#### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

3. **Start the FastAPI server**:
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser** to http://localhost:3000

## API Endpoints

### Diagrams
- `GET /api/diagrams/` - List all diagrams
- `GET /api/diagrams/{diagram_id}/summary` - Get diagram summary
- `GET /api/diagrams/{diagram_id}/graph` - Get graph data for visualization
- `DELETE /api/diagrams/{diagram_id}` - Delete a diagram

### Nodes
- `GET /api/nodes/` - List nodes with optional filtering
- `GET /api/nodes/{node_id}` - Get specific node details
- `GET /api/nodes/{node_id}/connections` - Get node connections
- `GET /api/nodes/types/list` - List all node types

### Edges
- `GET /api/edges/` - List edges with optional filtering
- `GET /api/edges/types/list` - List all edge types
- `GET /api/edges/protection-schemes` - Get protection schemes
- `GET /api/edges/paths/{from}/{to}` - Find paths between nodes

### Queries
- `POST /api/queries/execute` - Execute custom Cypher queries
- `GET /api/queries/examples` - Get example queries

## Environment Variables

### Backend
- `NEO4J_URI` - Neo4j connection URI (default: bolt://localhost:7687)
- `NEO4J_USERNAME` - Neo4j username (default: neo4j)
- `NEO4J_PASSWORD` - Neo4j password (default: password)
- `NEO4J_DATABASE` - Neo4j database name (default: neo4j)

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Development

### Backend Development

The backend uses FastAPI with automatic API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Development

The frontend uses:
- **Next.js 14** with App Router
- **React Flow** for graph visualization
- **Tailwind CSS** for styling
- **Shadcn/ui** for UI components
- **TypeScript** for type safety

### Adding New Features

1. **Backend**: Add new API routes in `backend/app/api/`
2. **Frontend**: Add new components in `frontend/src/components/`
3. **Types**: Update TypeScript types in `frontend/src/types/`

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the backend CORS settings include your frontend URL
2. **Connection Issues**: Check that Neo4j is running and accessible
3. **Build Errors**: Ensure all dependencies are installed correctly

### Logs

View service logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f neo4j
```

### Health Checks

- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000
- Neo4j: http://localhost:7474

## Production Deployment

For production deployment:

1. **Update environment variables** for production URLs
2. **Use production Docker images** or build optimized images
3. **Configure reverse proxy** (nginx) for SSL termination
4. **Set up monitoring** and logging
5. **Configure backup** for Neo4j data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the EA Analyzer suite and follows the same licensing terms.
