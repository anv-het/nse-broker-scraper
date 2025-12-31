/**
 * Frontend Configuration
 * ======================
 * Centralized configuration for the NSE Broker Dashboard frontend
 * This is the ONLY configuration file - no .env file is used
 */

// Frontend Configuration
const CONFIG = {
    // Server Configuration
    FRONTEND: {
        PORT: 1050,
        IP: '192.168.119.183',
        HOST: 'http://192.168.119.183:1050'
    },

    // Backend API Configuration
    BACKEND: {
        BASE_URL: 'http://192.168.119.183:8755',
        API_VERSION: 'v1',
        API_BASE_URL: 'http://192.168.119.183:8755/api/v1'
    },

    // Application Configuration
    APP: {
        NAME: 'NSE Broker Dashboard',
        VERSION: '1.0.0',
        ENVIRONMENT: 'development'
    },

    // Feature Flags
    FEATURES: {
        DEBUG_MODE: true,
        ANALYTICS: true,
        ERROR_LOGGING: true
    },

    // UI Configuration
    UI: {
        DEFAULT_PAGE_SIZE: 50,
        MAX_PAGE_SIZE: 200,
        ENABLE_DARK_MODE: false
    },

    // API Endpoints
    ENDPOINTS: {
        BROKERS: '/brokers',
        BROKERS_TOP: '/brokers/top',
        BROKERS_ANALYTICS: '/brokers/analytics',
        DASHBOARD_STATS: '/dashboard/stats',
        BROKER_DETAILS: '/brokers/details',
        AUTHORIZED_PERSONS: '/brokers/authorized-persons',
        DEALING_OFFICES: '/brokers/dealing-offices'
    }
};

// Utility functions
CONFIG.getFullUrl = (endpoint) => {
    return `${CONFIG.BACKEND.API_BASE_URL}${endpoint}`;
};

CONFIG.getBrokerDetailsUrl = (brokerId) => {
    return CONFIG.getFullUrl(`${CONFIG.ENDPOINTS.BROKER_DETAILS}/${brokerId}`);
};

CONFIG.getAuthorizedPersonsUrl = (brokerId) => {
    return CONFIG.getFullUrl(`${CONFIG.ENDPOINTS.AUTHORIZED_PERSONS}/${brokerId}`);
};

CONFIG.getDealingOfficesUrl = (brokerId) => {
    return CONFIG.getFullUrl(`${CONFIG.ENDPOINTS.DEALING_OFFICES}/${brokerId}`);
};

// Debug logging
if (CONFIG.FEATURES.DEBUG_MODE) {
    console.log('🔧 Frontend Configuration Loaded:', CONFIG);
}

// Export for use in other modules
window.CONFIG = CONFIG;
