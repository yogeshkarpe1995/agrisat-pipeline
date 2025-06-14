# Project Structure - Separation of Concerns

This document outlines the reorganized project structure following separation of concerns principles.

## Directory Structure

```
satellite-agriculture-monitoring/
├── src/                           # Main source code
│   ├── core/                      # Core business logic and configuration
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   └── pipeline.py            # Main pipeline orchestration
│   ├── data/                      # Data layer (database, models)
│   │   ├── __init__.py
│   │   ├── models.py              # Database models and schemas
│   │   └── database_manager.py    # Database operations and queries
│   ├── services/                  # External services and integrations
│   │   ├── __init__.py
│   │   ├── api_client.py          # External API communication
│   │   ├── auth.py                # Authentication with Copernicus
│   │   └── satellite_search.py    # Satellite data availability search
│   ├── processors/                # Data processing and computation
│   │   ├── __init__.py
│   │   ├── satellite_processor.py # Satellite image processing
│   │   └── indices_calculator.py  # Vegetation indices calculations
│   ├── api/                       # REST API endpoints
│   │   ├── __init__.py
│   │   └── server.py              # Flask API server
│   └── utils/                     # Utility functions and helpers
│       ├── __init__.py
│       └── helpers.py             # Common utility functions
├── scripts/                       # Standalone scripts
│   ├── create_database.py         # Database initialization
│   └── run_local.py               # Local development runner
├── tests/                         # Test files
│   └── test_api.py                # API testing
├── config/                        # Configuration files
│   └── database_schema.sql        # Database schema definition
├── docs/                          # Documentation
│   ├── API_REFERENCE.md
│   ├── DATABASE_SCHEMA.md
│   └── PIPELINE_PROCESSES.md
├── main.py                        # Main entry point for pipeline
├── api_server.py                  # Main entry point for API server
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration
└── README.md                      # Project documentation
```

## Separation of Concerns

### Core Layer (`src/core/`)
- **Responsibility**: Business logic, configuration, and pipeline orchestration
- **Files**: 
  - `config.py`: Application configuration and settings
  - `pipeline.py`: Main workflow orchestration and coordination

### Data Layer (`src/data/`)
- **Responsibility**: Data persistence, models, and database operations
- **Files**:
  - `models.py`: SQLAlchemy database models
  - `database_manager.py`: Database operations and queries

### Services Layer (`src/services/`)
- **Responsibility**: External integrations and third-party services
- **Files**:
  - `api_client.py`: External API communication
  - `auth.py`: Authentication with Copernicus Dataspace
  - `satellite_search.py`: Satellite data availability queries

### Processors Layer (`src/processors/`)
- **Responsibility**: Data processing and computational tasks
- **Files**:
  - `satellite_processor.py`: Satellite image processing
  - `indices_calculator.py`: Vegetation indices calculations

### API Layer (`src/api/`)
- **Responsibility**: REST API endpoints and web interface
- **Files**:
  - `server.py`: Flask application and API routes

### Utils Layer (`src/utils/`)
- **Responsibility**: Shared utility functions and helpers
- **Files**:
  - `helpers.py`: Common utility functions

## Entry Points

- **Pipeline**: `python main.py` - Runs the satellite monitoring pipeline
- **API Server**: `python api_server.py` - Starts the REST API server
- **Database Setup**: `python scripts/create_database.py` - Initializes the database
- **Local Development**: `python scripts/run_local.py` - Development utilities

## Import Structure

All imports now follow the new structure:
```python
from src.core.config import Config
from src.data.database_manager import DatabaseManager
from src.services.api_client import APIClient
from src.processors.satellite_processor import SatelliteProcessor
from src.api.server import app
from src.utils.helpers import validate_plot_data
```

## Benefits

1. **Clear Separation**: Each layer has a single responsibility
2. **Maintainability**: Easy to locate and modify specific functionality
3. **Testability**: Components can be tested in isolation
4. **Scalability**: Easy to add new features within appropriate layers
5. **Reusability**: Components can be reused across different parts of the application