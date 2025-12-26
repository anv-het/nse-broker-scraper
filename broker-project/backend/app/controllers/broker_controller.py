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
                    # Get latest period (last key in dictionary)
                    periods = list(data_by_period.keys())
                    if periods:
                        latest_period = periods[-1]
                        period_data = data_by_period[latest_period]
                        if isinstance(period_data, dict):
                            try:
                                active_clients = int(
                                    period_data.get("Total_number_of_active_clients", 0)
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
            
            # Aggregate to get top brokers
            pipeline = [
                {"$match": {"summary_trading_member_info.Data_By_Period": {"$exists": True}}},
                {"$project": {
                    "member_name": "$Member Name",
                    "member_code": "$Member Code",
                    "city": "$Registered_Office.City",
                    "latest_period": {"$arrayElemAt": [
                        {"$objectToArray": "$summary_trading_member_info.Data_By_Period"}, -1
                    ]}
                }},
                {"$project": {
                    "member_name": 1,
                    "member_code": 1,
                    "city": 1,
                    "active_clients": {"$toInt": {
                        "$ifNull": ["$latest_period.v.Total_number_of_active_clients", "0"]
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
