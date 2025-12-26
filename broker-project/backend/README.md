# NSE Broker Management System - Backend

## 🎯 Overview

A robust, scalable REST API backend for managing NSE (National Stock Exchange) broker data. Built with Flask, MongoDB, and modern Python practices. Provides comprehensive broker information including trading statistics, office details, management data, and analytics.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud instance)
- Git

### Installation

1. **Clone and Navigate**:
```powershell
cd broker-project/backend
```

2. **Install Dependencies**:
```powershell
pip install -r requirements.txt
```

3. **Configure Database**:
Edit `app/config/database.py` with your MongoDB connection string.

4. **Start Server**:
```powershell
python run_server.py
```

The server will start on:
- **URL**: http://192.168.119.183:8758
- **API Base**: http://192.168.119.183:8758/api/v1
- **Health Check**: http://192.168.119.183:8758/api/v1/health

---

## 📡 API Endpoints

### Dashboard Endpoints (Screen 1 - Broker List)

#### Get Broker List with Pagination
```
GET /api/v1/dashboard/brokers
```

**Query Parameters:**
- `page` (int, optional): Page number (default: 1)
- `limit` (int, optional): Records per page (default: 50, max: 200)
- `search` (string, optional): Search by broker name, SEBI reg, or member code
- `city` (string, optional): Filter by city

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "sr_no": "1",
      "member_name": "BROKER NAME",
      "sebi_reg_no": "INZ000123456",
      "member_code": "12345"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 28,
    "total_records": 1377,
    "per_page": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

#### Get Dashboard Statistics
```
GET /api/v1/dashboard/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_brokers": 1377,
    "detailed_brokers": 1377,
    "completion_percentage": 100.0,
    "cities_count": 99,
    "avg_active_clients": 23433,
    "total_active_clients": 32267716
  }
}
```

#### Get City Filters
```
GET /api/v1/dashboard/filters/cities
```

**Response:**
```json
{
  "success": true,
  "data": ["MUMBAI", "DELHI", "BANGALORE", "CHENNAI", "KOLKATA", ...]
}
```

---

### Analytics Endpoints (Screen 2 - Analytics Dashboard)

#### Get Broker Analytics Data
```
GET /api/v1/brokers/analytics
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "sr_no": 1,
      "member_name": "BROKER NAME",
      "member_code": "12345",
      "active_clients": 150,
      "city": "MUMBAI",
      "website": "https://example.com",
      "ceo_name": "CEO NAME",
      "compliance_officer": "OFFICER NAME"
    }
  ],
  "total_count": 1377
}
```

#### Get Top Brokers by Active Clients
```
GET /api/v1/brokers/top?limit=10
```

**Query Parameters:**
- `limit` (int, optional): Number of top brokers (default: 10, max: 100)

---

### Broker Details Endpoints (Screen 3 - Complete Details)

#### Get Complete Broker Details
```
GET /api/v1/brokers/{member_code}
```

**Path Parameters:**
- `member_code` (string, required): Broker's unique member code

**Response:**
```json
{
  "success": true,
  "data": {
    "Member Name": "ZERODHA BROKING LIMITED",
    "Member Code": "13906",
    "SEBI Registration no": "INZ000031633",
    "Basic_Details": {
      "Status": "Active",
      "Member Type": "Trading Member",
      "Incorporation Date": "2015-08-01"
    },
    "Registered_Office": {
      "Address": "153/154, 4th Cross, Dollars Colony, R.M.V. 2nd Stage, Bangalore - 560094",
      "City": "BANGALORE",
      "State": "KARNATAKA",
      "Phone": "+91-80-40402020"
    },
    "key_management_details": {
      "CEO": "Nithin Kamath",
      "Compliance Officer": "Anand Narayan",
      "Company Secretary": "Venkataramanan Mahadevan"
    },
    "trading_segments": {
      "Capital Market": "Active",
      "F&O": "Active",
      "Currency Derivatives": "Active",
      "Commodity Derivatives": "Inactive"
    },
    "directors": [
      {
        "name": "Nithin Kamath",
        "designation": "Director"
      }
    ],
    "complaints_data": {
      "total_complaints": 45,
      "resolved_complaints": 43,
      "pending_complaints": 2
    },
    "bank_accounts": [...],
    "net_worth": {
      "total_net_worth": "₹1,25,000",
      "last_updated": "2024-12-01"
    }
  }
}
```

#### Search Brokers
```
GET /api/v1/brokers/search?q=ZERODHA&limit=20
```

**Query Parameters:**
- `q` (string, required): Search query (name, SEBI reg, member code)
- `limit` (int, optional): Maximum results (default: 20, max: 100)

---

### Utility Endpoints

#### Health Check
```
GET /api/v1/health
```

**Response:**
```json
{
  "success": true,
  "service": "NSE Broker Management System",
  "version": "1.0.0",
  "database_connected": true,
  "status": "healthy",
  "timestamp": "2025-12-26T10:30:00Z"
}
```

---

## 🏗️ Architecture & Design

### Project Structure
```
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # Flask application factory
│   │
│   ├── controllers/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── dashboard_controller.py    # Dashboard operations
│   │   └── broker_controller.py       # Broker CRUD operations
│   │
│   ├── routes/                   # API routing layer
│   │   ├── __init__.py
│   │   └── api_router.py             # All API endpoints (400+ lines)
│   │
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py               # App settings & constants
│   │   └── database.py               # MongoDB connection manager
│   │
│   └── models/                   # Data models & schemas
│       ├── __init__.py
│       └── broker_model.py           # Broker data schemas
│
├── run_server.py                 # Server startup script
├── requirements.txt              # Python dependencies
├── README.md                     # This documentation
│
└── postman/                      # API testing collections
    └── NSE_Broker_API.postman_collection.json
```

### Architecture Pattern
- **MVC Pattern**: Model-View-Controller separation
- **Layered Architecture**: Routes → Controllers → Models → Database
- **Singleton Pattern**: Database connection management
- **Factory Pattern**: Flask application factory

### Data Flow
```
HTTP Request → Flask Route → Controller Method → Model Query
       ↓              ↓              ↓              ↓
   JSON Response ← Data Transform ← Business Logic ← MongoDB Query
```

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Server Configuration
FLASK_ENV=development
FLASK_DEBUG=True
HOST=192.168.119.183
PORT=8758

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/WEB_SCRAPING
DATABASE_NAME=WEB_SCRAPING
COLLECTION_NAME=Broker_list_details

# API Configuration
API_PREFIX=/api/v1
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=200
SEARCH_LIMIT=100

# CORS Configuration
CORS_ORIGINS=http://localhost:5050,http://192.168.119.183:5050
```

### Settings Configuration
Edit `app/config/settings.py`:

```python
# Application Settings
APP_NAME = "NSE Broker Management System"
APP_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# Pagination Settings
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
SEARCH_LIMIT = 100

# CORS Settings
CORS_ORIGINS = ["http://localhost:5050", "http://192.168.119.183:5050"]
```

### Database Configuration
Edit `app/config/database.py`:

```python
# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/WEB_SCRAPING"
DATABASE_NAME = "WEB_SCRAPING"
COLLECTION_NAME = "Broker_list_details"

# Connection Settings
CONNECTION_TIMEOUT = 5000
SERVER_SELECTION_TIMEOUT = 5000
```

---

## 🗄️ Database Schema

### MongoDB Collection: `Broker_list_details`

**Document Structure:**
```json
{
  "_id": ObjectId("..."),
  "sr_no": "1",
  "member_name": "ZERODHA BROKING LIMITED",
  "member_code": "13906",
  "sebi_reg_no": "INZ000031633",

  // Basic Details
  "Basic_Details": {
    "Status": "Active",
    "Member Type": "Trading Member",
    "Incorporation Date": "2015-08-01"
  },

  // Office Addresses
  "Registered_Office": {
    "Address": "153/154, 4th Cross...",
    "City": "BANGALORE",
    "State": "KARNATAKA",
    "Phone": "+91-80-40402020"
  },

  // Management
  "key_management_details": {
    "CEO": "Nithin Kamath",
    "Compliance Officer": "Anand Narayan"
  },

  // Trading Data
  "trading_segments": {
    "Capital Market": "Active",
    "F&O": "Active"
  },

  // Additional Data
  "directors": [...],
  "complaints_data": {...},
  "bank_accounts": [...],
  "net_worth": {...},

  // Metadata
  "scraped_at": "2025-12-26T10:30:00Z",
  "scraper_version": "2.1.0"
}
```

### Indexes
```javascript
// Performance indexes
db.Broker_list_details.createIndex({ "member_code": 1 }, { unique: true });
db.Broker_list_details.createIndex({ "member_name": 1 });
db.Broker_list_details.createIndex({ "sebi_reg_no": 1 });
db.Broker_list_details.createIndex({ "Basic_Details.Status": 1 });
db.Broker_list_details.createIndex({ "Registered_Office.City": 1 });
```

---

## 🔍 API Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

### Paginated Response
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "current_page": 1,
    "total_pages": 28,
    "total_records": 1377,
    "per_page": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 🧪 Testing

### Manual Testing with cURL

```powershell
# Health check
curl http://192.168.119.183:8758/api/v1/health

# Get dashboard stats
curl http://192.168.119.183:8758/api/v1/dashboard/stats

# Get paginated brokers
curl "http://192.168.119.183:8758/api/v1/dashboard/brokers?page=1&limit=10"

# Search brokers
curl "http://192.168.119.183:8758/api/v1/dashboard/brokers?search=ZERODHA"

# Filter by city
curl "http://192.168.119.183:8758/api/v1/dashboard/brokers?city=MUMBAI"

# Get broker details
curl http://192.168.119.183:8758/api/v1/brokers/13906

# Get analytics data
curl http://192.168.119.183:8758/api/v1/brokers/analytics

# Get top brokers
curl "http://192.168.119.183:8758/api/v1/brokers/top?limit=5"
```

### Automated Testing

```python
# test_api.py
import requests
import json

BASE_URL = "http://192.168.119.183:8758/api/v1"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["status"] == "healthy"

def test_broker_details():
    response = requests.get(f"{BASE_URL}/brokers/13906")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "data" in data

# Run tests
test_health()
test_broker_details()
print("All tests passed!")
```

---

## 📊 Performance & Monitoring

### Response Times (Typical)
- Health Check: < 50ms
- Dashboard Stats: < 100ms
- Broker List (50 items): < 200ms
- Broker Details: < 150ms
- Analytics Data: < 300ms

### Database Query Optimization
- **Indexes**: Optimized for common queries
- **Pagination**: Limits data transfer
- **Projection**: Returns only required fields
- **Connection Pooling**: Reuses database connections

### Monitoring Endpoints
```python
# Add to api_router.py
@api_router.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify({
        "uptime": get_uptime(),
        "total_requests": get_request_count(),
        "avg_response_time": get_avg_response_time(),
        "database_connections": get_db_connection_count()
    })
```

---

## 🚀 Production Deployment

### Using Gunicorn (Recommended)
```powershell
# Install Gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -b 192.168.119.183:8758 app.main:app

# With configuration file
gunicorn -c gunicorn.conf.py app.main:app
```

### Using Docker
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8758

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8758", "app.main:app"]
```

```powershell
# Build and run
docker build -t nse-broker-api .
docker run -p 8758:8758 nse-broker-api
```

### Environment Setup
```powershell
# Production environment variables
export FLASK_ENV=production
export MONGODB_URI=mongodb://prod-server:27017/WEB_SCRAPING
export HOST=0.0.0.0
export PORT=8758
```

---

## 🔒 Security Features

### CORS Protection
```python
from flask_cors import CORS
CORS(app, origins=settings.CORS_ORIGINS)
```

### Input Validation
```python
# In controllers
def validate_member_code(member_code):
    if not member_code or len(member_code) != 5:
        raise ValueError("Invalid member code format")

def sanitize_search_query(query):
    # Remove special characters, limit length
    return query.strip()[:100]
```

### Rate Limiting (Optional)
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@api_router.route('/brokers/search')
@limiter.limit("10 per minute")
def search_brokers():
    # Rate limited endpoint
```

---

## 📝 Development Workflow

### Adding New Endpoints

1. **Define Route** in `api_router.py`:
```python
@api_router.route('/brokers/export', methods=['GET'])
def export_brokers():
    # Implementation
```

2. **Add Controller Method** in appropriate controller:
```python
def export_brokers(format='json'):
    # Business logic
    pass
```

3. **Update Documentation** in README.md

### Database Schema Changes

1. **Update Model** in `broker_model.py`
2. **Create Migration Script** if needed
3. **Update Indexes** for performance
4. **Test Queries** with new schema

### Error Handling

```python
try:
    # Operation
    result = perform_operation()
    return jsonify({"success": True, "data": result})
except ValueError as e:
    return jsonify({"success": False, "error": str(e)}), 400
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return jsonify({"success": False, "error": "Internal server error"}), 500
```

---

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed**
```
Error: MongoDB connection timeout
Solution:
1. Check MongoDB service is running
2. Verify connection string in database.py
3. Check network connectivity
4. Update firewall rules
```

**Port Already in Use**
```
Error: [Errno 48] Address already in use
Solution:
1. Kill existing process: lsof -ti:8758 | xargs kill -9
2. Change port in settings.py
3. Use different host IP
```

**CORS Errors in Browser**
```
Error: CORS policy blocked
Solution:
1. Add frontend domain to CORS_ORIGINS in settings.py
2. Restart server
3. Check CORS headers in browser dev tools
```

**Memory Usage High**
```
Issue: Server consuming too much memory
Solution:
1. Reduce DEFAULT_PAGE_SIZE
2. Implement result caching
3. Use database pagination effectively
4. Monitor with memory profiler
```

---

## 📈 Scaling Considerations

### Horizontal Scaling
- **Load Balancer**: Distribute requests across multiple instances
- **Database Sharding**: Split data across multiple MongoDB instances
- **Caching Layer**: Redis for frequently accessed data

### Performance Optimization
- **Database Indexes**: Optimize query performance
- **Connection Pooling**: Reuse database connections
- **Async Operations**: Handle I/O operations asynchronously
- **Response Compression**: Gzip responses for large payloads

### Monitoring & Alerting
- **Health Checks**: Automated monitoring of service health
- **Metrics Collection**: Track response times, error rates
- **Log Aggregation**: Centralized logging system
- **Alert System**: Notifications for critical issues

---

## 🤝 Contributing

### Code Standards
- **PEP 8**: Python style guide compliance
- **Type Hints**: Use type annotations
- **Docstrings**: Comprehensive function documentation
- **Error Handling**: Proper exception handling
- **Logging**: Appropriate log levels

### Testing Standards
- **Unit Tests**: Test individual functions
- **Integration Tests**: Test API endpoints
- **Load Tests**: Performance under load
- **Edge Cases**: Test with invalid inputs

---

## 📞 Support & Contact

### Documentation
- **API Documentation**: This README.md
- **Postman Collection**: `postman/NSE_Broker_API.postman_collection.json`
- **Code Comments**: Inline documentation in all files

### Getting Help
1. Check this README for common issues
2. Review API response formats
3. Test with Postman collection
4. Check server logs for errors

### Reporting Issues
- Include full error messages
- Provide request/response examples
- Specify environment details
- Include steps to reproduce

---

## 📋 Change Log

### Version 1.0.0 (December 26, 2025)
- ✅ Initial release with full NSE broker API
- ✅ Dashboard, analytics, and details endpoints
- ✅ MongoDB integration with optimized queries
- ✅ Comprehensive error handling and logging
- ✅ Production-ready configuration
- ✅ Complete documentation and Postman collection

---

**Version**: 1.0.0  
**Last Updated**: December 26, 2025  
**Python Version**: 3.8+  
**Flask Version**: 2.3+  
**MongoDB Version**: 4.4+  
**License**: Proprietary
```json
{
  "success": true,
  "data": ["MUMBAI", "DELHI", "BANGALORE", ...]
}
```

---

### Analytics Endpoints (Screen 2)

#### Get Broker Analytics
```
GET /api/v1/brokers/analytics
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "sr_no": 1,
      "member_name": "BROKER NAME",
      "member_code": "12345",
      "active_clients": 150,
      "city": "MUMBAI",
      "website": "https://example.com",
      "ceo_name": "CEO NAME",
      "compliance_officer": "OFFICER NAME"
    }
  ],
  "total_count": 1377
}
```

#### Get Top Brokers
```
GET /api/v1/brokers/top?limit=10
```

**Query Parameters:**
- `limit` (int, optional): Number of top brokers (default: 10)

---

### Broker Details Endpoints (Screen 3)

#### Get Broker Details
```
GET /api/v1/brokers/{member_code}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "Member Name": "...",
    "Member Code": "...",
    "SEBI Registration no": "...",
    "Basic_Details": {...},
    "Registered_Office": {...},
    "key_management_details": {...},
    ...
  }
}
```

#### Search Brokers
```
GET /api/v1/brokers/search?q=ZERODHA&limit=20
```

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int, optional): Maximum results (default: 20)

---

### Utility Endpoints

#### Health Check
```
GET /api/v1/health
```

**Response:**
```json
{
  "success": true,
  "service": "NSE Broker Management System",
  "version": "1.0.0",
  "database_connected": true,
  "status": "healthy"
}
```

---

## 📁 Project Structure

```
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # Main Flask application
│   │
│   ├── controllers/              # Business logic
│   │   ├── __init__.py
│   │   ├── dashboard_controller.py    # Dashboard operations
│   │   └── broker_controller.py       # Broker operations
│   │
│   ├── routes/                   # API endpoints
│   │   ├── __init__.py
│   │   └── api_router.py             # All API routes
│   │
│   ├── config/                   # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py               # App settings
│   │   └── database.py               # DB connection
│   │
│   └── models/                   # Data models
│       ├── __init__.py
│       └── broker_model.py           # Broker schemas
│
├── run_server.py                 # Server startup script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🔧 Configuration

Edit `app/config/settings.py` to change:

- **Server**: Host and port
- **Database**: MongoDB connection string
- **API**: CORS origins, pagination settings

---

## 🧪 Testing

Test individual endpoints:

```powershell
# Health check
curl http://192.168.119.183:8758/api/v1/health

# Get stats
curl http://192.168.119.183:8758/api/v1/dashboard/stats

# Get brokers
curl "http://192.168.119.183:8758/api/v1/dashboard/brokers?page=1&limit=10"

# Get broker details
curl http://192.168.119.183:8758/api/v1/brokers/90456

# Search
curl "http://192.168.119.183:8758/api/v1/brokers/search?q=ZERODHA"
```

---

## 📝 Development Notes

### Architecture Pattern
- **MVC Pattern**: Separation of concerns
- **Controller Layer**: Business logic
- **Route Layer**: API endpoints
- **Model Layer**: Data schemas

### Database
- **MongoDB**: WEB_SCRAPING database
- **Collection**: Broker_list_details (1,377 documents)
- **Connection**: Managed by DatabaseManager singleton

### Error Handling
- All endpoints return consistent JSON responses
- HTTP status codes: 200 (success), 400 (bad request), 404 (not found), 500 (server error)

---

## 🚀 Production Deployment

For production, use a WSGI server like **Gunicorn**:

```powershell
pip install gunicorn
gunicorn -w 4 -b 192.168.119.183:8758 app.main:app
```

---

## 📞 Support

For issues or questions, contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: December 26, 2025
