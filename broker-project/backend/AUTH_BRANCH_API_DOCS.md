# NSE Broker Auth Person & Branch API Documentation

## 📋 Overview

This document provides comprehensive documentation for the NSE Broker Auth Person and Branch Office API endpoints. These APIs provide access to detailed authorized person data and dealing office information for NSE registered brokers.

### 🎯 Key Features

- **👤 Authorized Person Data**: Complete information about broker authorized persons
- **🏢 Branch Office Data**: Dealing office and branch location details  
- **🔍 Advanced Search**: Search across multiple fields with flexible matching
- **📊 Statistics**: Comprehensive analytics for both data types
- **📱 Multiple Access Methods**: Access by member code, mem_id, or direct search
- **⚡ High Performance**: Optimized queries with pagination support

### 📊 Data Sources

- **Auth Person Collection**: `Broker_member_Auth_Person`
- **Branch Office Collection**: `Broker_list_search_dealing_office`
- **Source Broker List**: `Broker_member_list`

---

## 🔐 Auth Person API Endpoints

### 1. Get Auth Person by Member Code

**Endpoint**: `GET /api/v1/brokers/{member_code}/auth-persons`

**Description**: Retrieve authorized person data for a specific broker using member code.

**Parameters**:
- `member_code` (path): Broker's unique member code (e.g., "90001")

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/brokers/90001/auth-persons" \
  -H "Accept: application/json"
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "broker_name": "ANGEL ONE LIMITED",
    "mem_id": "397",
    "member_code": "90001", 
    "authorized_persons": [
      {
        "sr.no": "1",
        "authorised_person_name": "JOHN DOE",
        "authorized_person_trade_name": "DOE TRADING",
        "registration_no.": "INZ000123456",
        "registration_date": "01-Jan-2020",
        "number_of_terminals": "5",
        "type_of_entity": "Individual",
        "ap_contact_person_name": "JOHN DOE",
        "ap_email_id": "john@example.com",
        "contact_no": "9876543210",
        "traded_segments": "EQUITY, FO",
        "status": "ACTIVE",
        "address": "123 Main Street",
        "city": "Mumbai", 
        "state": "Maharashtra",
        "pincode": "400001"
      }
    ]
  },
  "total_auth_persons": 1,
  "message": "Successfully retrieved auth person data for ANGEL ONE LIMITED"
}
```

### 2. Get Auth Person by Mem ID

**Endpoint**: `GET /api/v1/brokers/mem-id/{mem_id}/auth-persons`

**Description**: Retrieve authorized person data using internal mem_id.

**Parameters**:
- `mem_id` (path): Broker's internal mem_id (e.g., "397")

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/brokers/mem-id/397/auth-persons" \
  -H "Accept: application/json"
```

### 3. Get All Auth Persons (Paginated)

**Endpoint**: `GET /api/v1/auth-persons`

**Description**: Retrieve paginated list of all authorized person data.

**Query Parameters**:
- `page` (optional): Page number, default: 1
- `limit` (optional): Records per page, default: 50

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/auth-persons?page=1&limit=50" \
  -H "Accept: application/json"
```

**Example Response**:
```json
{
  "success": true,
  "data": [
    {
      "broker_name": "ANGEL ONE LIMITED",
      "authorized_persons": [...]
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 10,
    "total_records": 500,
    "records_per_page": 50,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  },
  "message": "Successfully retrieved 50 auth person records"
}
```

### 4. Search Auth Persons

**Endpoint**: `GET /api/v1/auth-persons/search`

**Description**: Search authorized person data by various criteria.

**Query Parameters**:
- `q` (required): Search query
- `limit` (optional): Maximum results, default: 20

**Search Fields**:
- Broker name
- Authorized person name
- Authorized person trade name
- Member code
- Mem ID

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/auth-persons/search?q=ANGEL&limit=10" \
  -H "Accept: application/json"
```

### 5. Get Auth Person Statistics

**Endpoint**: `GET /api/v1/auth-persons/statistics`

**Description**: Get comprehensive statistics about authorized person data.

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/auth-persons/statistics" \
  -H "Accept: application/json"
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "total_brokers_with_auth_data": 150,
    "total_authorized_persons": 450,
    "avg_auth_persons_per_broker": 3.0,
    "max_auth_persons_per_broker": 15,
    "min_auth_persons_per_broker": 1
  },
  "message": "Successfully retrieved auth person statistics"
}
```

---

## 🏢 Branch Office API Endpoints

### 1. Get Branch by Member Code

**Endpoint**: `GET /api/v1/brokers/{member_code}/branches`

**Description**: Retrieve dealing office data for a specific broker using member code.

**Parameters**:
- `member_code` (path): Broker's unique member code (e.g., "90001")

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/brokers/90001/branches" \
  -H "Accept: application/json"
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "broker_name": "ANGEL ONE LIMITED",
    "mem_id": "397",
    "member_code": "90001",
    "offices": [
      {
        "sr.no": "1",
        "office_type": "REGISTERED OFFICE",
        "contact_person_name": "JANE SMITH",
        "address": "601, CJ Tower, Netaji Subhash Place",
        "city": "NEW DELHI",
        "state": "DELHI", 
        "pincode": "110034"
      },
      {
        "sr.no": "2",
        "office_type": "BRANCH OFFICE",
        "contact_person_name": "RAJESH KUMAR",
        "address": "123 Business Plaza, Andheri East",
        "city": "MUMBAI",
        "state": "MAHARASHTRA",
        "pincode": "400069"
      }
    ]
  },
  "total_offices": 2,
  "message": "Successfully retrieved branch data for ANGEL ONE LIMITED"
}
```

### 2. Get Branch by Mem ID

**Endpoint**: `GET /api/v1/brokers/mem-id/{mem_id}/branches`

**Description**: Retrieve dealing office data using internal mem_id.

**Parameters**:
- `mem_id` (path): Broker's internal mem_id (e.g., "397")

### 3. Get All Branches (Paginated)

**Endpoint**: `GET /api/v1/branches`

**Description**: Retrieve paginated list of all dealing office data.

**Query Parameters**:
- `page` (optional): Page number, default: 1
- `limit` (optional): Records per page, default: 50

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/branches?page=1&limit=50" \
  -H "Accept: application/json"
```

### 4. Search Branches

**Endpoint**: `GET /api/v1/branches/search`

**Description**: Search dealing office data by various criteria.

**Query Parameters**:
- `q` (required): Search query
- `limit` (optional): Maximum results, default: 20

**Search Fields**:
- Broker name
- Office type
- Contact person name
- City
- State
- Address
- Member code
- Mem ID

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/branches/search?q=MUMBAI&limit=10" \
  -H "Accept: application/json"
```

### 5. Get Branches by City

**Endpoint**: `GET /api/v1/branches/city/{city}`

**Description**: Get dealing offices filtered by specific city.

**Parameters**:
- `city` (path): City name (e.g., "MUMBAI")

**Query Parameters**:
- `limit` (optional): Maximum results, default: 50

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/branches/city/MUMBAI?limit=25" \
  -H "Accept: application/json"
```

### 6. Get Branch Statistics

**Endpoint**: `GET /api/v1/branches/statistics`

**Description**: Get comprehensive statistics about dealing office data.

**Example Request**:
```bash
curl -X GET "http://192.168.119.183:8758/api/v1/branches/statistics" \
  -H "Accept: application/json"
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "total_brokers_with_branch_data": 200,
    "total_dealing_offices": 800,
    "unique_cities": 95,
    "unique_states": 28,
    "office_types": [
      "REGISTERED OFFICE",
      "BRANCH OFFICE", 
      "SUB OFFICE",
      "FRANCHISEE OFFICE"
    ],
    "brokers_with_offices": 200
  },
  "message": "Successfully retrieved branch office statistics"
}
```

---

## 📊 Data Models

### Auth Person Record Structure

```json
{
  "sr.no": "string",
  "authorised_person_name": "string",
  "authorized_person_trade_name": "string", 
  "registration_no.": "string",
  "registration_date": "string",
  "number_of_terminals": "string",
  "type_of_entity": "string",
  "ap_contact_person_name": "string",
  "ap_email_id": "string",
  "contact_no": "string", 
  "traded_segments": "string",
  "status": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "pincode": "string"
}
```

### Branch Office Record Structure

```json
{
  "sr.no": "string",
  "office_type": "string",
  "contact_person_name": "string",
  "address": "string",
  "city": "string", 
  "state": "string",
  "pincode": "string"
}
```

---

## ⚡ Performance & Optimization

### Response Times
- **Single Broker Queries**: < 100ms
- **Search Queries**: < 500ms
- **Paginated Lists**: < 300ms
- **Statistics**: < 1000ms

### Caching Strategy
- MongoDB connection pooling
- Optimized query indexes
- Efficient aggregation pipelines

### Rate Limiting
- No explicit rate limiting (production consideration)
- MongoDB connection limits apply

---

## 🔧 Error Handling

### Common Error Codes

#### 400 Bad Request
```json
{
  "success": false,
  "error": "Invalid parameters: page must be a positive integer"
}
```

#### 404 Not Found
```json
{
  "success": false, 
  "error": "No authorized person data found for member code: 12345",
  "code": "AUTH_PERSON_NOT_FOUND"
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal server error",
  "code": "INTERNAL_ERROR"
}
```

#### Database Connection Error
```json
{
  "success": false,
  "error": "Database connection failed",
  "code": "DB_CONNECTION_ERROR"
}
```

---

## 🧪 Testing

### Manual Testing with cURL

```bash
# Test auth person endpoint
curl -X GET "http://192.168.119.183:8758/api/v1/brokers/90001/auth-persons"

# Test branch endpoint
curl -X GET "http://192.168.119.183:8758/api/v1/brokers/90001/branches"

# Test search functionality  
curl -X GET "http://192.168.119.183:8758/api/v1/auth-persons/search?q=ANGEL&limit=5"

# Test statistics
curl -X GET "http://192.168.119.183:8758/api/v1/branches/statistics"
```

### Automated Testing

Run the provided test script:
```bash
cd broker-project/backend
python test_auth_branch_apis.py
```

---

## 📚 Integration Guide

### Frontend Integration

```javascript
// Get auth person data
async function getAuthPersonData(memberCode) {
  try {
    const response = await fetch(`/api/v1/brokers/${memberCode}/auth-persons`);
    const data = await response.json();
    
    if (data.success) {
      return data.data.authorized_persons;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Failed to fetch auth person data:', error);
    throw error;
  }
}

// Get branch data
async function getBranchData(memberCode) {
  try {
    const response = await fetch(`/api/v1/brokers/${memberCode}/branches`);
    const data = await response.json();
    
    if (data.success) {
      return data.data.offices;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Failed to fetch branch data:', error);
    throw error;
  }
}
```

### Postman Collection

Import the updated collection: `NSE_Broker_API.postman_collection.json`

Contains pre-configured requests for all endpoints with sample data and tests.

---

## 🔮 Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket support for live data updates
2. **Advanced Filtering**: Multi-criteria filtering with date ranges
3. **Export Functionality**: CSV/Excel export for search results
4. **Geocoding**: Latitude/longitude for branch locations
5. **Bulk Operations**: Batch requests for multiple brokers
6. **API Versioning**: v2 endpoints with enhanced features

### Performance Improvements

1. **Redis Caching**: Implement Redis for frequently accessed data
2. **GraphQL Support**: Alternative query interface
3. **Compression**: Response compression for large datasets
4. **CDN Integration**: Static asset optimization

---

## 📞 Support & Troubleshooting

### Common Issues

1. **Database Connection Failures**: Check MongoDB service status
2. **Empty Results**: Verify data exists in collections
3. **Slow Performance**: Check database indexes and connection pool
4. **Invalid Parameters**: Validate input parameters and types

### Debug Mode

Set environment variable for detailed logging:
```bash
export FLASK_DEBUG=True
export FLASK_ENV=development
```

### Health Check

Always start with health check endpoint:
```bash
curl http://192.168.119.183:8758/api/v1/health
```

---

*Last Updated: December 29, 2025*  
*Version: 2.0.0*  
*API Base URL: http://192.168.119.183:8758/api/v1*
