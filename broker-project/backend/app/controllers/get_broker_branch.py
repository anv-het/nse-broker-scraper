"""
Broker Branch (Dealing Office) Controller
========================================
Controller for handling NSE broker dealing office/branch data operations.
Provides APIs to fetch branch office data from MongoDB collection.
"""

from flask import current_app
from pymongo.errors import PyMongoError
from typing import Dict, List, Any, Optional
import logging
from bson import ObjectId

from ..config.database import DatabaseManager

# Configure logging
logger = logging.getLogger(__name__)


class BrokerBranchController:
    """Controller class for broker branch/dealing office operations."""
    
    def __init__(self):
        """Initialize the controller."""
        self.db_manager = DatabaseManager()
        self.collection_name = "Broker_list_search_dealing_office"
    
    def get_branch_by_member_code(self, member_code: str) -> Dict[str, Any]:
        """
        Get dealing office data for a specific broker by member code.
        
        Args:
            member_code (str): Broker member code
            
        Returns:
            Dict containing branch office data or error
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Find branch data by member_code
            branch_data = collection.find_one({"member_code": member_code})
            
            if not branch_data:
                return {
                    "success": False,
                    "error": f"No dealing office data found for member code: {member_code}",
                    "code": "BRANCH_NOT_FOUND"
                }
            
            # Convert ObjectId to string for JSON serialization
            if '_id' in branch_data:
                branch_data['_id'] = str(branch_data['_id'])
            
            return {
                "success": True,
                "data": branch_data,
                "total_offices": len(branch_data.get('offices', [])),
                "message": f"Successfully retrieved branch data for {branch_data.get('broker_name', 'Unknown')}"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_branch_by_member_code: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_branch_by_member_code: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
    
    def get_branch_by_mem_id(self, mem_id: str) -> Dict[str, Any]:
        """
        Get dealing office data for a specific broker by mem_id.
        
        Args:
            mem_id (str): Broker mem_id (internal ID)
            
        Returns:
            Dict containing branch office data or error
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Find branch data by mem_id
            branch_data = collection.find_one({"mem_id": mem_id})
            
            if not branch_data:
                return {
                    "success": False,
                    "error": f"No dealing office data found for mem_id: {mem_id}",
                    "code": "BRANCH_NOT_FOUND"
                }
            
            # Convert ObjectId to string for JSON serialization
            if '_id' in branch_data:
                branch_data['_id'] = str(branch_data['_id'])
            
            return {
                "success": True,
                "data": branch_data,
                "total_offices": len(branch_data.get('offices', [])),
                "message": f"Successfully retrieved branch data for {branch_data.get('broker_name', 'Unknown')}"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_branch_by_mem_id: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_branch_by_mem_id: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
    
    def get_all_branches(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get paginated list of all dealing office data.
        
        Args:
            page (int): Page number (1-based)
            limit (int): Records per page
            
        Returns:
            Dict containing paginated branch office data
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Calculate skip value for pagination
            skip = (page - 1) * limit
            
            # Get total count
            total_count = collection.count_documents({})
            
            # Get paginated data
            branch_data_cursor = collection.find({}).skip(skip).limit(limit)
            branch_data_list = []
            
            for doc in branch_data_cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                branch_data_list.append(doc)
            
            # Calculate pagination metadata
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "success": True,
                "data": branch_data_list,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_records": total_count,
                    "records_per_page": limit,
                    "has_next": has_next,
                    "has_prev": has_prev,
                    "next_page": page + 1 if has_next else None,
                    "prev_page": page - 1 if has_prev else None
                },
                "message": f"Successfully retrieved {len(branch_data_list)} branch office records"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_all_branches: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_all_branches: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
    
    def search_branches(self, search_term: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search dealing office data by broker name, office type, city, or contact person.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum results to return
            
        Returns:
            Dict containing matching branch office data
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Create search query with regex for flexible matching
            search_query = {
                "$or": [
                    {"broker_name": {"$regex": search_term, "$options": "i"}},
                    {"offices.office_type": {"$regex": search_term, "$options": "i"}},
                    {"offices.contact_person_name": {"$regex": search_term, "$options": "i"}},
                    {"offices.city": {"$regex": search_term, "$options": "i"}},
                    {"offices.state": {"$regex": search_term, "$options": "i"}},
                    {"offices.address": {"$regex": search_term, "$options": "i"}},
                    {"member_code": {"$regex": search_term, "$options": "i"}},
                    {"mem_id": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            # Execute search with limit
            branch_data_cursor = collection.find(search_query).limit(limit)
            branch_data_list = []
            
            for doc in branch_data_cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                branch_data_list.append(doc)
            
            return {
                "success": True,
                "data": branch_data_list,
                "total_found": len(branch_data_list),
                "search_term": search_term,
                "message": f"Found {len(branch_data_list)} branch office records matching '{search_term}'"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in search_branches: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in search_branches: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
    
    def get_branches_by_city(self, city: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get dealing offices filtered by city.
        
        Args:
            city (str): City name
            limit (int): Maximum results to return
            
        Returns:
            Dict containing branch office data for the specified city
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Create query to filter by city
            city_query = {"offices.city": {"$regex": city, "$options": "i"}}
            
            # Execute query with limit
            branch_data_cursor = collection.find(city_query).limit(limit)
            branch_data_list = []
            
            for doc in branch_data_cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                branch_data_list.append(doc)
            
            return {
                "success": True,
                "data": branch_data_list,
                "total_found": len(branch_data_list),
                "city": city,
                "message": f"Found {len(branch_data_list)} brokers with offices in '{city}'"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_branches_by_city: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_branches_by_city: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
    
    def get_branch_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about dealing office data.
        
        Returns:
            Dict containing branch office statistics
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Get basic stats
            total_brokers = collection.count_documents({})
            
            # Get aggregated stats
            pipeline = [
                {
                    "$project": {
                        "broker_name": 1,
                        "member_code": 1,
                        "office_count": {"$size": {"$ifNull": ["$offices", []]}},
                        "offices": 1
                    }
                },
                {
                    "$unwind": {
                        "path": "$offices",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_offices": {"$sum": 1},
                        "unique_cities": {"$addToSet": "$offices.city"},
                        "unique_states": {"$addToSet": "$offices.state"},
                        "office_types": {"$addToSet": "$offices.office_type"},
                        "brokers_with_offices": {"$addToSet": "$broker_name"}
                    }
                },
                {
                    "$project": {
                        "total_offices": 1,
                        "total_unique_cities": {"$size": "$unique_cities"},
                        "total_unique_states": {"$size": "$unique_states"},
                        "office_types": 1,
                        "brokers_with_offices_count": {"$size": "$brokers_with_offices"}
                    }
                }
            ]
            
            stats_result = list(collection.aggregate(pipeline))
            
            if stats_result:
                stats = stats_result[0]
                return {
                    "success": True,
                    "data": {
                        "total_brokers_with_branch_data": total_brokers,
                        "total_dealing_offices": stats.get("total_offices", 0),
                        "unique_cities": stats.get("total_unique_cities", 0),
                        "unique_states": stats.get("total_unique_states", 0),
                        "office_types": list(stats.get("office_types", [])),
                        "brokers_with_offices": stats.get("brokers_with_offices_count", 0)
                    },
                    "message": "Successfully retrieved branch office statistics"
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "total_brokers_with_branch_data": total_brokers,
                        "total_dealing_offices": 0,
                        "unique_cities": 0,
                        "unique_states": 0,
                        "office_types": [],
                        "brokers_with_offices": 0
                    },
                    "message": "No branch office data found"
                }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_branch_statistics: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_branch_statistics: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }


# Initialize controller instance
branch_controller = BrokerBranchController()

# Function exports for use in routes
def get_branch_by_member_code(member_code: str) -> Dict[str, Any]:
    """Get branch data by member code."""
    return branch_controller.get_branch_by_member_code(member_code)

def get_branch_by_mem_id(mem_id: str) -> Dict[str, Any]:
    """Get branch data by mem_id."""
    return branch_controller.get_branch_by_mem_id(mem_id)

def get_all_branches(page: int = 1, limit: int = 50) -> Dict[str, Any]:
    """Get paginated list of all branch data."""
    return branch_controller.get_all_branches(page, limit)

def search_branches(search_term: str, limit: int = 20) -> Dict[str, Any]:
    """Search branch data."""
    return branch_controller.search_branches(search_term, limit)

def get_branches_by_city(city: str, limit: int = 50) -> Dict[str, Any]:
    """Get branches filtered by city."""
    return branch_controller.get_branches_by_city(city, limit)

def get_branch_statistics() -> Dict[str, Any]:
    """Get branch statistics."""
    return branch_controller.get_branch_statistics()
