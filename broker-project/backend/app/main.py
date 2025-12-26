"""
NSE Broker Management System - Main Application
================================================
Flask application entry point.

Author: Development Team
Version: 1.0.0
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

from .config import settings, db_manager
from .routes import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Application factory pattern.
    Creates and configures the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, origins=settings.CORS_ORIGINS)
    
    # Register blueprints
    app.register_blueprint(api_router)
    
    # Root endpoint
    @app.route('/')
    def root():
        """Root endpoint - API information."""
        return jsonify({
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "documentation": {
                "base_url": f"http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}",
                "endpoints": {
                    "dashboard_brokers": f"{settings.API_PREFIX}/dashboard/brokers",
                    "dashboard_stats": f"{settings.API_PREFIX}/dashboard/stats",
                    "city_filters": f"{settings.API_PREFIX}/dashboard/filters/cities",
                    "broker_analytics": f"{settings.API_PREFIX}/brokers/analytics",
                    "top_brokers": f"{settings.API_PREFIX}/brokers/top",
                    "broker_details": f"{settings.API_PREFIX}/brokers/<member_code>",
                    "search_brokers": f"{settings.API_PREFIX}/brokers/search",
                    "health_check": f"{settings.API_PREFIX}/health"
                }
            }
        })
    
    # Startup event
    @app.before_request
    def before_first_request():
        """Ensure database connection before first request."""
        if not db_manager.is_connected():
            db_manager.connect()
    
    # Shutdown event
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Cleanup on shutdown."""
        pass
    
    return app


def run_server():
    """
    Run the Flask development server.
    """
    print("=" * 80)
    print(f"🚀 {settings.APP_NAME}")
    print(f"📦 Version: {settings.APP_VERSION}")
    print("=" * 80)
    print(f"🌐 Server starting on: http://{settings.HOST}:{settings.PORT}")
    print(f"📡 API Base URL: http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}")
    print("=" * 80)
    print("\n📋 Available Endpoints:")
    print(f"   • Dashboard Brokers: {settings.API_PREFIX}/dashboard/brokers")
    print(f"   • Dashboard Stats: {settings.API_PREFIX}/dashboard/stats")
    print(f"   • City Filters: {settings.API_PREFIX}/dashboard/filters/cities")
    print(f"   • Broker Analytics: {settings.API_PREFIX}/brokers/analytics")
    print(f"   • Top Brokers: {settings.API_PREFIX}/brokers/top")
    print(f"   • Broker Details: {settings.API_PREFIX}/brokers/<member_code>")
    print(f"   • Search Brokers: {settings.API_PREFIX}/brokers/search")
    print(f"   • Health Check: {settings.API_PREFIX}/health")
    print("=" * 80)
    print(f"\n💾 Database: {settings.MONGO_DB_NAME}")
    print(f"📊 Collection: {settings.MONGO_COLLECTION_LIST}")
    print("=" * 80)
    print("\n✅ Server is ready! Press CTRL+C to stop.\n")
    
    # Create and run app
    app = create_app()
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )


# Create app instance
app = create_app()

if __name__ == '__main__':
    run_server()
