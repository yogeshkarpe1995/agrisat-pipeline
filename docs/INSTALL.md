
# Local Installation Guide

This guide explains how to set up and run the Satellite Agriculture Monitoring Pipeline on your local environment.

## Prerequisites

- Python 3.8 or higher
- Git
- At least 2GB of free disk space

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd satellite-agriculture-monitoring
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install the package with all dependencies:

```bash
pip install -e .
```

### 3. Environment Variables

Create a `.env` file in the project root directory:

```bash
# Copernicus Dataspace credentials
COPERNICUS_CLIENT_ID=cdse-public
COPERNICUS_CLIENT_SECRET=your_secret_here
COPERNICUS_USERNAME=your_username_here
COPERNICUS_PASSWORD=your_password_here

# Database configuration
DATABASE_URL=sqlite:///satellite_monitoring.db

# Flask configuration
FLASK_SECRET_KEY=your_random_secret_key_here
```

### 4. Create Database

Initialize the database with sample data:

```bash
python create_database.py
```

### 5. Verify Installation

Test the API server:

```bash
python api_server.py
```

The API should be available at http://0.0.0.0:5000

Test the pipeline:

```bash
python main.py
```

## Running the Services

### Start the API Server

```bash
python api_server.py
```

The API will be available at:
- Local: http://0.0.0.0:5000
- Health check: http://0.0.0.0:5000/api/health

### Run the Satellite Pipeline

```bash
python main.py
```

This will:
1. Fetch plot data from the API
2. Download satellite imagery
3. Process images and calculate vegetation indices
4. Save results to the `output/` directory

### Run Both Services (Development)

You can run both services simultaneously using separate terminals:

**Terminal 1 (API Server):**
```bash
python api_server.py
```

**Terminal 2 (Pipeline):**
```bash
python main.py
```

## Project Structure

```
satellite-agriculture-monitoring/
├── output/                    # Generated satellite data outputs
├── docs/                     # Documentation
├── *.py                      # Python modules
├── requirements.txt          # Dependencies
├── setup.py                 # Package setup
├── INSTALL.md              # This file
├── README.md               # Project overview
└── satellite_monitoring.db # SQLite database
```

## Troubleshooting

### Common Issues

1. **Missing dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Database errors:**
   ```bash
   rm satellite_monitoring.db
   python create_database.py
   ```

3. **Permission errors on Linux/Mac:**
   ```bash
   chmod +x create_database.py
   chmod +x main.py
   chmod +x api_server.py
   ```

4. **Port conflicts:**
   - Change port in `api_server.py` if 5000 is already in use
   - Check running processes: `lsof -i :5000`

### Logs

Check logs for debugging:
- Pipeline logs: `pipeline.log`
- API logs: Console output

### Data Verification

Verify the setup:

```bash
# Check database
python -c "from database_manager import DatabaseManager; dm = DatabaseManager(); print(f'Plots: {len(dm.get_plot_metadata())}')"

# Check API
curl http://0.0.0.0:5000/api/health

# Check output directory
ls -la output/
```

## Development

### Running Tests

```bash
python test_api.py
```

### Adding New Dependencies

1. Add to `requirements.txt`
2. Update `setup.py` if needed
3. Run `pip install -r requirements.txt`

## Support

For issues and questions:
1. Check the logs (`pipeline.log`)
2. Verify environment variables
3. Ensure all dependencies are installed
4. Check network connectivity for satellite data downloads
