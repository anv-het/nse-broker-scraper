"""
API Router
==========
Central API routing configuration.
Defines all API endpoints and maps them to controller functions.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from ..controllers import dashboard_controller, broker_controller
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api_router = Blueprint('api', __name__, url_prefix=settings.API_PREFIX)


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@api_router.route('/dashboard/brokers', methods=['GET'])
def get_dashboard_brokers():
    """
    Get broker list for dashboard (Screen 1).
    
    Query Parameters:
        - page: Page number (default: 1)
        - limit: Records per page (default: 50)
        - search: Search term (optional)
        - city: Filter by city (optional)
    
    Returns:
        JSON response with broker list and pagination
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', settings.DEFAULT_PAGE_SIZE))
        search = request.args.get('search', None)
        city = request.args.get('city', None)
        
        # Call controller
        result = dashboard_controller.get_broker_list(
            page=page,
            limit=limit,
            search=search,
            city=city
        )
        
        return jsonify(result), 200 if result.get('success') else 500
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid parameters: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error in get_dashboard_brokers: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@api_router.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get dashboard statistics.
    
    Returns:
        JSON response with statistics
    """
    try:
        result = dashboard_controller.get_dashboard_stats()
        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        logger.error(f"Error in get_dashboard_stats: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@api_router.route('/dashboard/filters/cities', methods=['GET'])
def get_city_filters():
    """
    Get unique cities for filtering.
    
    Returns:
        JSON response with list of cities
    """
    try:
        result = dashboard_controller.get_city_filters()
        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        logger.error(f"Error in get_city_filters: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


# ============================================================================
# BROKER ANALYTICS ROUTES (Screen 2 - Analytics Tab)
# ============================================================================

@api_router.route('/brokers/analytics', methods=['GET'])
def get_broker_analytics():
    """
    Get broker analytics data (Screen 2).
    Shows: Sr No, Broker Name, Active Clients, City, Website, CEO, Compliance Officer
    
    Returns:
        JSON response with analytics data
    """
    try:
        result = broker_controller.get_broker_analytics()
        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        logger.error(f"Error in get_broker_analytics: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@api_router.route('/brokers/top', methods=['GET'])
def get_top_brokers():
    """
    Get top brokers by active clients.
    
    Query Parameters:
        - limit: Number of top brokers (default: 10)
    
    Returns:
        JSON response with top brokers
    """
    try:
        limit = int(request.args.get('limit', 10))
        result = broker_controller.get_top_brokers_by_clients(limit=limit)
        return jsonify(result), 200 if result.get('success') else 500
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid limit parameter: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error in get_top_brokers: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


# ============================================================================
# BROKER DETAILS ROUTES (Screen 3 - Full Details)
# ============================================================================

@api_router.route('/brokers/<string:member_code>', methods=['GET'])
def get_broker_details(member_code: str):
    """
    Get complete broker details by member code (Screen 3).
    
    Args:
        member_code: Broker's member code
    
    Returns:
        JSON response with complete broker information
    """
    try:
        result = broker_controller.get_broker_details(member_code)
        return jsonify(result), 200 if result.get('success') else 404
    except Exception as e:
        logger.error(f"Error in get_broker_details: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@api_router.route('/brokers/search', methods=['GET'])
def search_brokers():
    """
    Search brokers by name, SEBI reg, or member code.
    
    Query Parameters:
        - q: Search query (required)
        - limit: Maximum results (default: 20)
    
    Returns:
        JSON response with matching brokers
    """
    try:
        search_query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not search_query:
            return jsonify({
                "success": False,
                "error": "Search query 'q' is required"
            }), 400
        
        result = broker_controller.search_brokers(
            search_term=search_query,
            limit=limit
        )
        return jsonify(result), 200 if result.get('success') else 500
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid parameters: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error in search_brokers: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


# ============================================================================
# HEALTH CHECK ROUTE
# ============================================================================

@api_router.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with service status
    """
    from ..config import db_manager
    
    is_db_connected = db_manager.is_connected()
    
    return jsonify({
        "success": True,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_connected": is_db_connected,
        "status": "healthy" if is_db_connected else "degraded"
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@api_router.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@api_router.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500
