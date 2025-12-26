"""
Dashboard Controller
====================
Business logic for dashboard operations.
Handles broker list display with pagination, search, and filtering.
"""

from typing import Dict, List, Optional, Any
from pymongo.collection import Collection
import logging

from ..config import get_broker_collection, settings

logger = logging.getLogger(__name__)


class DashboardController:
    """Controller for dashboard operations."""
    
    @staticmethod
    def get_broker_list(
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated broker list with optional filters.
        
        Args:
            page: Page number (starts from 1)
            limit: Number of records per page
            search: Search term for member name, SEBI reg, or member code
            city: Filter by city name
            
        Returns:
            dict: Response with broker data and pagination info
        """
        try:
            collection = get_broker_collection()
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "data": [],
                    "pagination": {}
                }
            
            # Build query
            query = {}
            
            # Search filter
            if search and search.strip():
                search_term = search.strip()
                query["$or"] = [
                    {"Member Name": {"$regex": search_term, "$options": "i"}},
                    {"SEBI Registration no": {"$regex": search_term, "$options": "i"}},
                    {"Member Code": {"$regex": search_term, "$options": "i"}},
                    {"_metadata.member_name": {"$regex": search_term, "$options": "i"}}
                ]
            
            # City filter
            if city and city.strip():
                query["Registered_Office.City"] = city.strip()
            
            # Get total count
            total_records = collection.count_documents(query)
            
            # Calculate pagination
            limit = min(limit, settings.MAX_PAGE_SIZE)  # Enforce max limit
            total_pages = (total_records + limit - 1) // limit if total_records > 0 else 0
            skip = (page - 1) * limit
            
            # Fetch brokers with pagination
            # Use aggregation pipeline to convert sr_no to number and sort properly
            pipeline = [
                {"$match": query},
                {"$addFields": {
                    "sr_no_numeric": {"$toInt": "$_metadata.sr_no"}
                }},
                {"$sort": {"sr_no_numeric": 1}},
                {"$skip": skip},
                {"$limit": limit},
                {"$project": {
                    "_id": 1,
                    "Member Name": 1,
                    "Member Code": 1,
                    "SEBI Registration no": 1,
                    "_metadata": 1,
                    "Basic_Details": 1
                }}
            ]
            
            brokers = list(collection.aggregate(pipeline))
            
            # Process broker data
            broker_list = []
            for broker in brokers:
                broker_item = {
                    "sr_no": broker.get("_metadata", {}).get("sr_no", "-"),
                    "member_name": broker.get("Member Name", "-"),
                    "sebi_reg_no": broker.get("SEBI Registration no", "-"),
                    "member_code": broker.get("Member Code", "-")
                }
                broker_list.append(broker_item)
            
            return {
                "success": True,
                "data": broker_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_records": total_records,
                    "per_page": limit,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_broker_list: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "pagination": {}
            }
    
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """
        Get dashboard statistics.
        
        Returns:
            dict: Statistics including total brokers, cities, etc.
        """
        try:
            collection = get_broker_collection()
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed"
                }
            
            # Get total brokers
            total_brokers = collection.count_documents({})
            
            # Count brokers with detailed info (has active clients data)
            detailed_brokers = collection.count_documents({
                "summary_trading_member_info.Data_By_Period": {"$exists": True}
            })
            
            # Get unique cities
            cities = collection.distinct("Registered_Office.City")
            cities_count = len([c for c in cities if c])
            
            # Calculate average active clients
            pipeline = [
                {"$match": {"summary_trading_member_info.Data_By_Period": {"$exists": True}}},
                {"$project": {
                    "latest_period": {"$arrayElemAt": [
                        {"$objectToArray": "$summary_trading_member_info.Data_By_Period"}, -1
                    ]}
                }},
                {"$project": {
                    "active_clients": {"$toInt": {
                        "$ifNull": ["$latest_period.v.Total_number_of_active_clients", "0"]
                    }}
                }},
                {"$group": {
                    "_id": None,
                    "avg_clients": {"$avg": "$active_clients"},
                    "total_clients": {"$sum": "$active_clients"}
                }}
            ]
            
            stats_result = list(collection.aggregate(pipeline))
            avg_active_clients = int(stats_result[0]["avg_clients"]) if stats_result else 0
            total_active_clients = stats_result[0]["total_clients"] if stats_result else 0
            
            # Calculate completion percentage
            completion_percentage = round(
                (detailed_brokers / total_brokers * 100), 1
            ) if total_brokers > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "total_brokers": total_brokers,
                    "detailed_brokers": detailed_brokers,
                    "completion_percentage": completion_percentage,
                    "cities_count": cities_count,
                    "avg_active_clients": avg_active_clients,
                    "total_active_clients": total_active_clients
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_dashboard_stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_city_filters() -> Dict[str, Any]:
        """
        Get unique cities for filtering.
        
        Returns:
            dict: List of unique city names
        """
        try:
            collection = get_broker_collection()
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "data": []
                }
            
            # Get distinct cities
            cities = collection.distinct("Registered_Office.City")
            cities = sorted([city for city in cities if city])
            
            return {
                "success": True,
                "data": cities
            }
            
        except Exception as e:
            logger.error(f"Error in get_city_filters: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }


# Create controller instance
dashboard_controller = DashboardController()
