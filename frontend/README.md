# NSE Broker Data Viewer

A full-stack web application to view and search NSE broker information with beautiful UI and smooth interactions.

## Features

### Frontend
- 📊 **Broker List Page** - Display all brokers with pagination (50 per page)
- 🔍 **Search & Filter** - Search by name, filter by state and city
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎨 **Beautiful UI** - Modern gradient design with smooth animations
- 🚀 **Fast & Smooth** - Optimized performance with debounced search

### Backend API
- ✅ **RESTful API** - Clean and well-documented endpoints
- 🗄️ **MongoDB Integration** - Fetch detailed broker data from database
- 📄 **CSV Support** - Read broker list from CSV file
- 🔧 **Flexible Filtering** - Filter by city, state, name, and search term
- 📊 **Statistics** - Get broker data statistics and completion rate

## Project Structure

```
.
├── frontend/
│   ├── index.html          # Broker list page
│   ├── details.html        # Broker details page
│   ├── styles.css          # Shared styles
│   ├── script.js           # List page JavaScript
│   └── details.js          # Details page JavaScript
├── api_server.py           # Flask API server
├── nse_members.csv         # Broker list data
└── README.md              # This file
```

## Setup Instructions

### Prerequisites
- Python 3.7+
- MongoDB running on `192.168.102.120:27017`
- Modern web browser

### Installation

1. **Install Python Dependencies**
   ```powershell
   pip install flask flask-cors pymongo pandas
   ```

2. **Verify Data Files**
   - Ensure `nse_members.csv` exists in the root directory
   - Ensure MongoDB has broker details in `WEB_SCRAPING.Broker_list_details`

### Running the Application

1. **Start the API Server**
   ```powershell
   python api_server.py
   ```
   
   The API server will start at: http://localhost:5000

2. **Open the Frontend**
   - Open `frontend/index.html` in your web browser
   - Or use a local HTTP server:
     ```powershell
     cd frontend
     python -m http.server 8000
     ```
   - Then navigate to: http://localhost:8000

## API Endpoints

### Health Check
```
GET /api/health
```
Returns server status and MongoDB connection status.

### Get Broker List
```
GET /api/brokers?page=1&limit=50&search=&city=&state=
```
**Query Parameters:**
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 50)
- `search` - Search term for broker name
- `city` - Filter by city
- `state` - Filter by state

**Response:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "current_page": 1,
    "total_pages": 28,
    "total_records": 1379,
    "per_page": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

### Get Broker Details
```
GET /api/broker/<member_code>
```
Returns detailed information about a specific broker from MongoDB.

### Get Filter Options
```
GET /api/filters/cities
GET /api/filters/states
```
Returns list of available cities/states for filtering.

### Get Statistics
```
GET /api/stats
```
Returns overall statistics about broker data.

## Usage

### Broker List Page
1. Browse the broker list with pagination
2. Use the search box to find brokers by name
3. Filter by state and city using dropdown menus
4. Click "Clear Filters" to reset all filters
5. Click on broker name or "View Details" to see detailed information

### Broker Details Page
1. View comprehensive broker information organized in cards:
   - Basic Information
   - Registered Office details
   - Communication Office (if available)
   - Business Activities
   - Branch Offices
   - Compliance Information
   - Additional Information
2. Click "Back to List" to return to the broker list

## Data Mapping

The application maps broker data using:
- **Primary Key**: `member_code` (links CSV list to MongoDB details)
- **Secondary Keys**: `sr_no`, `sebi_reg_no`, `internal_id`

## Configuration

### API Server (`api_server.py`)
```python
MONGO_URI = "mongodb://sa:963852@192.168.102.120:27017/"
MONGO_DB_NAME = "WEB_SCRAPING"
MONGO_COLLECTION_NAME = "Broker_list_details"
CSV_FILE = "nse_members.csv"
```

### Frontend (`script.js` and `details.js`)
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

## Troubleshooting

### API Server not connecting to MongoDB
- Verify MongoDB is running: `192.168.102.120:27017`
- Check credentials: `sa:963852`
- Verify database and collection names

### Frontend can't reach API
- Ensure API server is running on port 5000
- Check CORS settings in `api_server.py`
- Update `API_BASE_URL` in JavaScript files if needed

### CSV file not found
- Ensure `nse_members.csv` is in the root directory
- Check file permissions

### No data showing in details page
- Verify MongoDB has data for the specific member_code
- Check browser console for errors
- Verify member_code format (string vs integer)

## Technologies Used

### Frontend
- HTML5
- CSS3 (with gradients and animations)
- Vanilla JavaScript (no frameworks)
- Responsive design with CSS Grid and Flexbox

### Backend
- Python 3
- Flask (web framework)
- Flask-CORS (cross-origin support)
- PyMongo (MongoDB driver)
- Pandas (CSV handling)

## Performance Optimizations

- Debounced search input (500ms delay)
- Pagination for large datasets (50 items per page)
- Efficient MongoDB queries with projections
- CSS animations for smooth transitions
- Lazy loading of filter options

## Future Enhancements

- [ ] Export broker data to Excel/PDF
- [ ] Advanced filtering (multiple states/cities)
- [ ] Sorting by column headers
- [ ] Bookmark favorite brokers
- [ ] Compare multiple brokers
- [ ] Dark mode toggle
- [ ] Mobile app version

## License

This project is for internal use only.

## Support

For issues or questions, please contact the development team.
