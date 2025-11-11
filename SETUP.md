# Setup Guide for LLM Benchmark API & Frontend

This guide will help you set up the REST API backend and Vue.js frontend for the LLM Benchmark project.

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- MongoDB (running locally or remotely)

## Step 1: Install Python Dependencies

```bash
# Activate your virtual environment (if using one)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Set Up MongoDB

### Option A: Local MongoDB Installation

```bash
# Ubuntu/Debian
sudo apt-get install mongodb
sudo systemctl start mongod

# macOS (using Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Windows
# Download and install from https://www.mongodb.com/try/download/community
```

### Option B: Docker

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Option C: MongoDB Atlas (Cloud)

Use MongoDB Atlas and set the connection string in your environment variables.

## Step 3: Configure Environment (Optional)

Create a `.env` file in the project root:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=llm_benchmark
API_HOST=0.0.0.0
API_PORT=8000
```

Or export environment variables:

```bash
export MONGODB_URL=mongodb://localhost:27017
export MONGODB_DB_NAME=llm_benchmark
export API_HOST=0.0.0.0
export API_PORT=8000
```

## Step 4: Start the API Server

```bash
python3 run_api.py
```

The API will be available at `http://localhost:8000`

You can test it by visiting:
- `http://localhost:8000/health` - Health check
- `http://localhost:8000/docs` - Interactive API documentation (Swagger UI)

## Step 5: Set Up and Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Step 6: Access the Application

1. Open your browser and go to `http://localhost:3000`
2. You should see the LLM Benchmark Dashboard
3. Fill in the form to start a new benchmark
4. View the results in the dashboard

## Troubleshooting

### MongoDB Connection Issues

- Make sure MongoDB is running: `sudo systemctl status mongod` (Linux) or check Docker container
- Verify connection string: `mongodb://localhost:27017`
- Check MongoDB logs for errors

### API Server Issues

- Check if port 8000 is available: `lsof -i :8000`
- Verify Python dependencies are installed: `pip list | grep fastapi`
- Check API logs for error messages

### Frontend Issues

- Make sure Node.js is installed: `node --version`
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check browser console for errors
- Verify the API proxy is working (check `vite.config.js`)

### CORS Issues

If you encounter CORS errors, make sure:
- The API server is running
- The frontend proxy is configured correctly in `vite.config.js`
- CORS middleware is enabled in `api/main.py`

## Development

### Running in Development Mode

Both the API and frontend support hot-reload:

- API: Uses `uvicorn` with `reload=True` (already configured in `run_api.py`)
- Frontend: Uses Vite's dev server with HMR (Hot Module Replacement)

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# The built files will be in frontend/dist/
# You can serve them with any static file server or integrate with your API server
```

## Next Steps

- Read the main README.md for usage examples
- Explore the API documentation at `http://localhost:8000/docs`
- Check out the benchmark visualization features in the frontend

