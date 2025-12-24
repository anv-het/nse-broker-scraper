"""
NSE Broker Data API Server
Flask API for serving broker list and details
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import pandas as pd
import os
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configuration
MONGO_URI = "mongodb://sa:963852@192.168.102.120:27017/"
MONGO_DB_NAME = "WEB_SCRAPING"
MONGO_COLLECTION_NAME = "Broker_list_details"
CSV_FILE = "nse_members.csv"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    db = mongo_client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    logger.info("✓ Connected to MongoDB")
except Exception as e:
    logger.error(f"✗ Failed to connect to MongoDB: {e}")
    collection = None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "mongodb_connected": collection is not None
    })


@app.route('/api/brokers', methods=['GET'])
def get_brokers():
    """
    Get broker list from CSV with pagination, search, and filters
    Query params:
    - page: page number (default: 1)
    - limit: items per page (default: 50)
    - search: search term (searches in member_name, member_code, sebi_reg_no)
    - city: filter by city (from MongoDB data)
    - state: filter by state (from MongoDB data)
    """
    try:
        # Read CSV file
        if not os.path.exists(CSV_FILE):
            return jsonify({"error": "CSV file not found"}), 404
        
        df = pd.read_csv(CSV_FILE)
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '').strip().lower()
        city_filter = request.args.get('city', '').strip()
        state_filter = request.args.get('state', '').strip()
        
        # Apply search filter - search in multiple columns
        if search:
            mask = (
                df['member_name'].astype(str).str.lower().str.contains(search, na=False) |
                df['member_code'].astype(str).str.lower().str.contains(search, na=False) |
                df['sebi_reg_no'].astype(str).str.lower().str.contains(search, na=False)
            )
            df = df[mask]
        
        # If city or state filter is provided, we need to join with MongoDB data
        if (city_filter or state_filter) and collection is not None:
            # Get member codes that match the filter from MongoDB
            mongo_query = {}
            if city_filter:
                mongo_query['Registered_Office.City'] = {'$regex': city_filter, '$options': 'i'}
            if state_filter:
                # Try to find state in Registered_Office (note: state might not be directly available)
                # We'll search in the address or city field
                mongo_query['$or'] = [
                    {'Registered_Office.City': {'$regex': state_filter, '$options': 'i'}},
                    {'Registered_Office.Registered Office Address': {'$regex': state_filter, '$options': 'i'}}
                ]
            
            # Get matching member codes
            matching_docs = collection.find(mongo_query, {'Member Code': 1})
            matching_codes = [str(doc.get('Member Code')) for doc in matching_docs if doc.get('Member Code')]
            
            # Filter dataframe
            df = df[df['member_code'].astype(str).isin(matching_codes)]
        
        # Calculate pagination
        total_records = len(df)
        total_pages = (total_records + limit - 1) // limit  # Ceiling division
        
        # Validate page number
        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_df = df.iloc[start_idx:end_idx]
        
        # Convert to list of dictionaries
        brokers = paginated_df.to_dict('records')
        
        return jsonify({
            "success": True,
            "data": brokers,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records,
                "per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_brokers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/broker/<member_code>', methods=['GET'])
def get_broker_details(member_code):
    """
    Get detailed broker information from MongoDB by member_code
    Tries multiple field names and formats to find the broker
    """
    try:
        if collection is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        
        # Try multiple query variations to find the broker
        broker_data = None
        
        # Try 1: Search by "Member Code" field (as string)
        broker_data = collection.find_one({"Member Code": member_code})
        
        # Try 2: Search by "member_code" field (lowercase)
        if not broker_data:
            broker_data = collection.find_one({"member_code": member_code})
        
        # Try 3: Try as integer
        if not broker_data:
            try:
                broker_data = collection.find_one({"Member Code": int(member_code)})
            except:
                pass
        
        # Try 4: Try as string with leading zeros stripped
        if not broker_data:
            try:
                broker_data = collection.find_one({"Member Code": str(int(member_code))})
            except:
                pass
        
        # Try 5: Search in Basic_Details
        if not broker_data:
            broker_data = collection.find_one({"Basic_Details.Member Code": member_code})
        
        if not broker_data:
            logger.warning(f"Broker not found for member_code: {member_code}")
            return jsonify({
                "success": False,
                "error": f"Broker details not found for member code: {member_code}",
                "message": "This broker may not have been scraped yet or the data is not available in the database."
            }), 404
        
        # Remove MongoDB _id field
        if '_id' in broker_data:
            broker_data['_id'] = str(broker_data['_id'])
        
        return jsonify({
            "success": True,
            "data": broker_data
        })
        
    except Exception as e:
        logger.error(f"Error in get_broker_details for {member_code}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/filters/cities', methods=['GET'])
def get_cities():
    """Get unique cities from MongoDB for filter dropdown"""
    try:
        if collection is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        
        # Get distinct cities - try multiple field paths
        cities = set()
        
        # Try different field names
        try:
            cities.update(collection.distinct('Registered_Office.City'))
        except:
            pass
        
        try:
            cities.update(collection.distinct('registered_office.city'))
        except:
            pass
        
        try:
            cities.update(collection.distinct('Correspondence_Office.City'))
        except:
            pass
        
        # Remove None/empty values and convert to sorted list
        cities = [city for city in cities if city and city.strip()]
        cities.sort()
        
        return jsonify({
            "success": True,
            "data": cities
        })
        
    except Exception as e:
        logger.error(f"Error in get_cities: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/filters/states', methods=['GET'])
def get_states():
    """Get unique states from MongoDB for filter dropdown"""
    try:
        if collection is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        
        # Since state is not directly stored, we'll extract unique states from city names
        # Or return empty for now - states can be added later if available
        states = []
        
        # Common Indian states to filter
        common_states = [
            "Maharashtra", "Delhi", "Karnataka", "Gujarat", "Tamil Nadu",
            "West Bengal", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh",
            "Telangana", "Andhra Pradesh", "Kerala", "Punjab", "Haryana"
        ]
        
        return jsonify({
            "success": True,
            "data": common_states
        })
        
    except Exception as e:
        logger.error(f"Error in get_states: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the broker data"""
    try:
        # CSV stats
        csv_count = 0
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            csv_count = len(df)
        
        # MongoDB stats
        mongo_count = 0
        if collection is not None:
            mongo_count = collection.count_documents({})
        
        return jsonify({
            "success": True,
            "data": {
                "total_brokers": csv_count,
                "detailed_brokers": mongo_count,
                "completion_percentage": round((mongo_count / csv_count * 100) if csv_count > 0 else 0, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 NSE Broker Data API Server")
    print("=" * 60)
    print(f"📡 Server running at: http://localhost:5000")
    print(f"📊 API Endpoints:")
    print(f"   - GET  /api/health              - Health check")
    print(f"   - GET  /api/brokers             - List all brokers (with pagination)")
    print(f"   - GET  /api/broker/<code>       - Get broker details")
    print(f"   - GET  /api/filters/cities      - Get all cities")
    print(f"   - GET  /api/filters/states      - Get all states")
    print(f"   - GET  /api/stats               - Get statistics")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
