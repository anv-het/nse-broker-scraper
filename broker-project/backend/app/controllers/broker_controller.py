"""
Broker Controller
=================
Business logic for individual broker operations.
Handles detailed broker information, analytics, and full broker profiles.
"""

from typing import Dict, List, Optional, Any
from pymongo.collection import Collection
import logging

from ..config import get_broker_collection

logger = logging.getLogger(__name__)


class BrokerController:
    """Controller for broker-specific operations."""
    
    @staticmethod
    def _get_latest_period_data(data_by_period: Dict) -> tuple:
        """
        Helper method to get the chronologically latest period data.
        
        Args:
            data_by_period: Dictionary of period data (e.g., "SEP 2025": {...})
            
        Returns:
            tuple: (period_key, period_data) of the most recent period
        """
        if not data_by_period:
            return None, {}
        
        # Create sortable dates from period keys
        periods_with_dates = []
        for period_key in data_by_period.keys():
            parts = period_key.split()
            if len(parts) == 2:
                month_str, year_str = parts
                # Convert month to number
                month_map = {
                    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
                    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
                }
                month_num = month_map.get(month_str, 1)
                try:
                    year_num = int(year_str)
                    sort_date = year_num * 100 + month_num
                    periods_with_dates.append((sort_date, period_key))
                except ValueError:
                    periods_with_dates.append((0, period_key))
        
        if not periods_with_dates:
            return None, {}
        
        # Sort by date (most recent first)
        periods_with_dates.sort(key=lambda x: x[0], reverse=True)
        latest_period_key = periods_with_dates[0][1]
        
        return latest_period_key, data_by_period.get(latest_period_key, {})
    
    @staticmethod
    def get_broker_details(member_code: str) -> Dict[str, Any]:
        """
        Get complete broker details by member code.
        
        Args:
            member_code: Broker's member code
            
        Returns:
            dict: Complete broker information
        """
        try:
            collection = get_broker_collection()
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed"
                }
            
            # Find broker by member code
            broker = collection.find_one({"Member Code": member_code})
            
            if not broker:
                return {
                    "success": False,
                    "error": f"Broker with member code {member_code} not found"
                }
            
            # Convert ObjectId to string
            broker["_id"] = str(broker["_id"])
            
            return {
                "success": True,
                "data": broker
            }
            
        except Exception as e:
            logger.error(f"Error in get_broker_details: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_broker_analytics() -> Dict[str, Any]:
        """
        Get analytics data for all brokers (for analytics dashboard/tab 2).
        Shows active clients, city, website, CEO, compliance officer.
        
        Returns:
            dict: Analytics data with broker performance metrics
        """
        try:
            collection = get_broker_collection()
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "data": []
                }
            
            # Fetch all brokers with required fields
            brokers = collection.find({}, {
                "_id": 0,
                "Member Name": 1,
                "Member Code": 1,
                "_metadata": 1,
                "summary_trading_member_info": 1,
                "Registered_Office": 1,
                "website_app": 1,
                "key_management_details": 1
            })
            
            analytics_data = []
            
            for broker in brokers:
                # Extract sr_no
                sr_no = broker.get("_metadata", {}).get("sr_no", 0)
                
                # Extract member name
                member_name = broker.get("Member Name", "-")
                
                # Extract member code
                member_code = broker.get("Member Code", "-")
                
                # Extract active clients from latest period
                active_clients = 0
                summary_info = broker.get("summary_trading_member_info", {})
                data_by_period = summary_info.get("Data_By_Period", {})
                if data_by_period:
                    # Get chronologically latest period
                    latest_period_key, latest_period_data = BrokerController._get_latest_period_data(data_by_period)
                    if latest_period_data:
                        try:
                            active_clients = int(
                                latest_period_data.get("Total_number_of_active_clients", 0)
                            )
                        except (ValueError, TypeError):
                            active_clients = 0
                
                # Extract city
                city = broker.get("Registered_Office", {}).get("City", "-")
                
                # Extract website
                website = broker.get("website_app", {}).get("Website Address", "-")
                
                # Extract CEO name
                ceo_name = "-"
                key_mgmt = broker.get("key_management_details", {})
                if isinstance(key_mgmt, dict):
                    md_ceo = key_mgmt.get("Managing_Director_CEO", {})
                    if isinstance(md_ceo, dict):
                        ceo_name = md_ceo.get("Name", "-")
                
                # Extract compliance officer
                compliance_officer = "-"
                if isinstance(key_mgmt, dict):
                    comp_officer = key_mgmt.get("Compliance_Officer", {})
                    if isinstance(comp_officer, dict):
                        compliance_officer = comp_officer.get("Name", "-")
                
                analytics_item = {
                    "sr_no": sr_no,
                    "member_name": member_name,
                    "member_code": member_code,
                    "active_clients": active_clients,
                    "city": city if city else "-",
                    "website": website if website else "-",
                    "ceo_name": ceo_name if ceo_name else "-",
                    "compliance_officer": compliance_officer if compliance_officer else "-"
                }
                
                analytics_data.append(analytics_item)
            
            # Sort by sr_no
            analytics_data.sort(key=lambda x: int(x["sr_no"]) if str(x["sr_no"]).isdigit() else 999999)
            
            return {
                "success": True,
                "data": analytics_data,
                "total_count": len(analytics_data)
            }
            
        except Exception as e:
            logger.error(f"Error in get_broker_analytics: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    @staticmethod
    def get_top_brokers_by_clients(limit: int = 10) -> Dict[str, Any]:
        """
        Get top brokers by active clients count.
        
        Args:
            limit: Number of top brokers to return
            
        Returns:
            dict: Top brokers sorted by active clients
        """
        try:
            collection = get_broker_collection()
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "data": []
                }
            
            # Aggregate to get top brokers with chronologically latest period
            pipeline = [
                {"$match": {"summary_trading_member_info.Data_By_Period": {"$exists": True}}},
                {"$project": {
                    "member_name": "$Member Name",
                    "member_code": "$Member Code",
                    "city": "$Registered_Office.City",
                    "periods_array": {"$objectToArray": "$summary_trading_member_info.Data_By_Period"}
                }},
                {"$unwind": "$periods_array"},
                {"$addFields": {
                    "period_key": "$periods_array.k",
                    "period_data": "$periods_array.v",
                    # Create a sortable date field from period key (e.g., "SEP 2025" -> 202509)
                    "sort_date": {
                        "$add": [
                            {"$multiply": [
                                {"$toInt": {"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 1]}}, 
                                100
                            ]},
                            {"$switch": {
                                "branches": [
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "JAN"]}, "then": 1},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "FEB"]}, "then": 2},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "MAR"]}, "then": 3},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "APR"]}, "then": 4},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "MAY"]}, "then": 5},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "JUN"]}, "then": 6},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "JUL"]}, "then": 7},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "AUG"]}, "then": 8},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "SEP"]}, "then": 9},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "OCT"]}, "then": 10},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "NOV"]}, "then": 11},
                                    {"case": {"$eq": [{"$arrayElemAt": [{"$split": ["$periods_array.k", " "]}, 0]}, "DEC"]}, "then": 12}
                                ],
                                "default": 1
                            }}
                        ]
                    }
                }},
                {"$sort": {"_id": 1, "sort_date": -1}},
                {"$group": {
                    "_id": "$_id",
                    "member_name": {"$first": "$member_name"},
                    "member_code": {"$first": "$member_code"},
                    "city": {"$first": "$city"},
                    "latest_period_data": {"$first": "$period_data"},
                    "latest_period_key": {"$first": "$period_key"}
                }},
                {"$project": {
                    "member_name": 1,
                    "member_code": 1,
                    "city": 1,
                    "latest_period": "$latest_period_key",
                    "active_clients": {"$toInt": {
                        "$ifNull": ["$latest_period_data.Total_number_of_active_clients", "0"]
                    }}
                }},
                {"$sort": {"active_clients": -1}},
                {"$limit": limit}
            ]
            
            top_brokers = list(collection.aggregate(pipeline))
            
            # Convert ObjectId to string
            for broker in top_brokers:
                broker["_id"] = str(broker["_id"])
            
            return {
                "success": True,
                "data": top_brokers
            }
            
        except Exception as e:
            logger.error(f"Error in get_top_brokers_by_clients: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    @staticmethod
    def search_brokers(search_term: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search brokers by name, SEBI registration, or member code.
        
        Args:
            search_term: Search query string
            limit: Maximum number of results
            
        Returns:
            dict: Matching brokers
        """
        try:
            collection = get_broker_collection()
            if collection is None:
                return {
                    "success": False,
                    "error": "Database connection failed",
                    "data": []
                }
            
            if not search_term or not search_term.strip():
                return {
                    "success": False,
                    "error": "Search term is required",
                    "data": []
                }
            
            search_term = search_term.strip()
            
            # Search query
            query = {"$or": [
                {"Member Name": {"$regex": search_term, "$options": "i"}},
                {"SEBI Registration no": {"$regex": search_term, "$options": "i"}},
                {"Member Code": {"$regex": search_term, "$options": "i"}}
            ]}
            
            # Find matching brokers
            brokers = list(collection.find(query, {
                "_id": 0,
                "Member Name": 1,
                "Member Code": 1,
                "SEBI Registration no": 1,
                "_metadata.sr_no": 1,
                "Registered_Office.City": 1
            }).limit(limit))
            
            return {
                "success": True,
                "data": brokers,
                "count": len(brokers)
            }
            
        except Exception as e:
            logger.error(f"Error in search_brokers: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }


# Create controller instance
broker_controller = BrokerController()
