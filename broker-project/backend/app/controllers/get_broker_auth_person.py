"""
Broker Auth Person Controller
============================
Controller for handling NSE broker authorized person data operations.
Provides APIs to fetch auth person data from MongoDB collection.
"""

from flask import current_app
from pymongo.errors import PyMongoError
from typing import Dict, List, Any, Optional
import logging
from bson import ObjectId

from ..config.database import DatabaseManager

# Configure logging
logger = logging.getLogger(__name__)


class BrokerAuthPersonController:
    """Controller class for broker auth person operations."""
    
    def __init__(self):
        """Initialize the controller."""
        self.db_manager = DatabaseManager()
        self.collection_name = "Broker_member_Auth_Person"
    
    def get_auth_person_by_member_code(self, member_code: str) -> Dict[str, Any]:
        """
        Get authorized person data for a specific broker by member code.
        
        Args:
            member_code (str): Broker member code
            
        Returns:
            Dict containing auth person data or error
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Find auth person data by member_code
            auth_data = collection.find_one({"member_code": member_code})
            
            if not auth_data:
                return {
                    "success": False,
                    "error": f"No authorized person data found for member code: {member_code}",
                    "code": "AUTH_PERSON_NOT_FOUND"
                }
            
            # Convert ObjectId to string for JSON serialization
            if '_id' in auth_data:
                auth_data['_id'] = str(auth_data['_id'])
            
            return {
                "success": True,
                "data": auth_data,
                "total_auth_persons": len(auth_data.get('authorized_persons', [])),
                "message": f"Successfully retrieved authorized person data for {auth_data.get('broker_name', 'Unknown')}"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_auth_person_by_member_code: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_auth_person_by_member_code: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
    
    def get_auth_person_by_mem_id(self, mem_id: str) -> Dict[str, Any]:
        """
        Get authorized person data for a specific broker by mem_id.
        
        Args:
            mem_id (str): Broker mem_id (internal ID)
            
        Returns:
            Dict containing auth person data or error
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Find auth person data by mem_id
            auth_data = collection.find_one({"mem_id": mem_id})
            
            if not auth_data:
                return {
                    "success": False,
                    "error": f"No authorized person data found for mem_id: {mem_id}",
                    "code": "AUTH_PERSON_NOT_FOUND"
                }
            
            # Convert ObjectId to string for JSON serialization
            if '_id' in auth_data:
                auth_data['_id'] = str(auth_data['_id'])
            
            return {
                "success": True,
                "data": auth_data,
                "total_auth_persons": len(auth_data.get('authorized_persons', [])),
                "message": f"Successfully retrieved authorized person data for {auth_data.get('broker_name', 'Unknown')}"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_auth_person_by_mem_id: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_auth_person_by_mem_id: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }

    def get_all_auth_persons(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get all authorized person data with pagination.
        
        Args:
            page (int): Page number (default: 1)
            limit (int): Records per page (default: 50)
            
        Returns:
            Dict containing paginated auth person data or error
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Calculate skip value
            skip = (page - 1) * limit
            
            # Get total count
            total_count = collection.count_documents({})
            
            # Get paginated results
            auth_data_list = list(collection.find({}).skip(skip).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for auth_data in auth_data_list:
                if '_id' in auth_data:
                    auth_data['_id'] = str(auth_data['_id'])
            
            return {
                "success": True,
                "data": auth_data_list,
                "pagination": {
                    "current_page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                    "has_next": page * limit < total_count,
                    "has_previous": page > 1
                },
                "message": f"Successfully retrieved {len(auth_data_list)} broker auth person records"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_all_auth_persons: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_all_auth_persons: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }

    def search_auth_persons(self, search_query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search authorized person data by broker name, person name, or city.
        
        Args:
            search_query (str): Search term
            limit (int): Maximum number of results
            
        Returns:
            Dict containing search results or error
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Create search filter
            search_filter = {
                "$or": [
                    {"broker_name": {"$regex": search_query, "$options": "i"}},
                    {"authorized_persons.authorised_person_name": {"$regex": search_query, "$options": "i"}},
                    {"authorized_persons.city": {"$regex": search_query, "$options": "i"}},
                    {"authorized_persons.state": {"$regex": search_query, "$options": "i"}},
                    {"member_code": {"$regex": search_query, "$options": "i"}}
                ]
            }
            
            # Execute search with limit
            auth_data_list = list(collection.find(search_filter).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for auth_data in auth_data_list:
                if '_id' in auth_data:
                    auth_data['_id'] = str(auth_data['_id'])
            
            return {
                "success": True,
                "data": auth_data_list,
                "count": len(auth_data_list),
                "search_query": search_query,
                "message": f"Found {len(auth_data_list)} results for '{search_query}'"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in search_auth_persons: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in search_auth_persons: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }

    def get_auth_person_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about authorized person data.
        
        Returns:
            Dict containing statistics or error
        """
        try:
            collection = self.db_manager.get_collection(self.collection_name)
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "code": "DB_CONNECTION_ERROR"
                }
            
            # Aggregation pipeline to get statistics
            pipeline = [
                {
                    "$project": {
                        "broker_name": 1,
                        "member_code": 1,
                        "mem_id": 1,
                        "authorized_persons": 1,
                        "total_auth_persons": {"$size": "$authorized_persons"},
                        "auth_person_cities": "$authorized_persons.city",
                        "auth_person_states": "$authorized_persons.state",
                        "entity_types": "$authorized_persons.type_of_entity",
                        "trading_segments": "$authorized_persons.traded_segments"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_brokers_with_auth_data": {"$sum": 1},
                        "total_authorized_persons": {"$sum": "$total_auth_persons"},
                        "all_cities": {"$push": "$auth_person_cities"},
                        "all_states": {"$push": "$auth_person_states"},
                        "all_entity_types": {"$push": "$entity_types"},
                        "all_trading_segments": {"$push": "$trading_segments"},
                        "brokers_with_auth_persons": {
                            "$sum": {
                                "$cond": [{"$gt": ["$total_auth_persons", 0]}, 1, 0]
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "total_brokers_with_auth_data": 1,
                        "total_authorized_persons": 1,
                        "brokers_with_auth_persons": 1,
                        "unique_cities": {
                            "$size": {
                                "$setUnion": {
                                    "$reduce": {
                                        "input": "$all_cities",
                                        "initialValue": [],
                                        "in": {"$setUnion": ["$$value", "$$this"]}
                                    }
                                }
                            }
                        },
                        "unique_states": {
                            "$size": {
                                "$setUnion": {
                                    "$reduce": {
                                        "input": "$all_states",
                                        "initialValue": [],
                                        "in": {"$setUnion": ["$$value", "$$this"]}
                                    }
                                }
                            }
                        },
                        "entity_types": {
                            "$setUnion": {
                                "$reduce": {
                                    "input": "$all_entity_types",
                                    "initialValue": [],
                                    "in": {"$setUnion": ["$$value", "$$this"]}
                                }
                            }
                        },
                        "unique_trading_segments": {
                            "$setUnion": {
                                "$reduce": {
                                    "input": "$all_trading_segments",
                                    "initialValue": [],
                                    "in": {"$setUnion": ["$$value", "$$this"]}
                                }
                            }
                        }
                    }
                }
            ]
            
            # Execute aggregation
            result = list(collection.aggregate(pipeline))
            
            if not result:
                stats = {
                    "total_brokers_with_auth_data": 0,
                    "total_authorized_persons": 0,
                    "brokers_with_auth_persons": 0,
                    "unique_cities": 0,
                    "unique_states": 0,
                    "entity_types": [],
                    "unique_trading_segments": []
                }
            else:
                stats = result[0]
            
            return {
                "success": True,
                "data": stats,
                "message": "Successfully retrieved authorized person statistics"
            }
            
        except PyMongoError as e:
            logger.error(f"MongoDB error in get_auth_person_statistics: {e}")
            return {
                "success": False,
                "error": "Database operation failed",
                "code": "DB_OPERATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_auth_person_statistics: {e}")
            return {
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR"
            }


# Initialize controller instance
auth_controller = BrokerAuthPersonController()

# Function exports for use in routes  
def get_auth_person_by_member_code(member_code: str) -> Dict[str, Any]:
    """Get auth person data by member code.""" 
    return auth_controller.get_auth_person_by_member_code(member_code)

def get_auth_person_by_mem_id(mem_id: str) -> Dict[str, Any]:
    """Get auth person data by mem_id."""
    return auth_controller.get_auth_person_by_mem_id(mem_id)

def get_all_auth_persons(page: int = 1, limit: int = 50) -> Dict[str, Any]:
    """Get paginated list of all auth person data."""
    return auth_controller.get_all_auth_persons(page, limit)

def search_auth_persons(search_term: str, limit: int = 20) -> Dict[str, Any]:
    """Search auth person data."""
    return auth_controller.search_auth_persons(search_term, limit)

def get_auth_person_statistics() -> Dict[str, Any]:
    """Get auth person statistics."""
    return auth_controller.get_auth_person_statistics()
