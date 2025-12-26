/**
 * Analytics Dashboard (Screen 2) - JavaScript
 * ==========================================
 * Handles broker analytics display with sorting and filtering
 */

// Configuration
const API_BASE_URL = 'http://192.168.119.183:8755/api/v1';

// State Management
let allBrokers = [];
let filteredBrokers = [];
let currentSort = { by: 'active_clients', order: 'desc' };

// DOM Elements
const loadingSpinner = document.getElementById('loadingSpinner');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const tableContainer = document.getElementById('tableContainer');
const analyticsTableBody = document.getElementById('analyticsTableBody');
const resultsInfo = document.getElementById('resultsInfo');
const resultsCount = document.getElementById('resultsCount');
const searchInput = document.getElementById('searchInput');
const sortBy = document.getElementById('sortBy');
const sortOrder = document.getElementById('sortOrder');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Analytics Dashboard initializing...');
    loadStatistics();
    loadAnalyticsData();
    
    // Add search with debounce
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(applyFilters, 300);
    });
});

/**
 * Load Dashboard Statistics
 */
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats`);
        const data = await response.json();
        
        if (data.success && data.data) {
            document.getElementById('totalBrokers').textContent = formatNumber(data.data.total_brokers);
            document.getElementById('totalClients').textContent = formatNumber(data.data.total_active_clients);
            document.getElementById('avgClients').textContent = formatNumber(data.data.avg_active_clients);
            document.getElementById('citiesCount').textContent = formatNumber(data.data.cities_count);
        }
    } catch (error) {
        console.error('❌ Error loading statistics:', error);
    }
}

/**
 * Load Analytics Data
 */
async function loadAnalyticsData() {
    showLoading(true);
    hideError();
    
    try {
        console.log('📡 Fetching analytics data...');
        const response = await fetch(`${API_BASE_URL}/brokers/analytics`);
        const data = await response.json();
        
        if (data.success && data.data) {
            allBrokers = data.data;
            console.log(`✅ Loaded ${allBrokers.length} brokers`);
            applyFilters();
        } else {
            showError(data.error || 'Failed to load analytics data');
        }
    } catch (error) {
        console.error('❌ Error loading analytics:', error);
        showError('Failed to connect to server. Please ensure the backend is running.');
    } finally {
        showLoading(false);
    }
}

/**
 * Apply Filters and Sorting
 */
function applyFilters() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    currentSort.by = sortBy.value;
    currentSort.order = sortOrder.value;
    
    // Filter brokers
    filteredBrokers = allBrokers.filter(broker => {
        if (!searchTerm) return true;
        
        const nameMatch = broker.member_name.toLowerCase().includes(searchTerm);
        const cityMatch = broker.city.toLowerCase().includes(searchTerm);
        const ceoMatch = broker.ceo_name.toLowerCase().includes(searchTerm);
        
        return nameMatch || cityMatch || ceoMatch;
    });
    
    // Sort brokers
    sortBrokers();
    
    // Display results
    displayAnalytics();
    updateSortIndicators();
}

/**
 * Sort Brokers
 */
function sortBrokers() {
    const sortField = currentSort.by;
    const isAscending = currentSort.order === 'asc';
    
    filteredBrokers.sort((a, b) => {
        let aVal, bVal;
        
        switch (sortField) {
            case 'sr_no':
                aVal = parseInt(a.sr_no) || 0;
                bVal = parseInt(b.sr_no) || 0;
                break;
            case 'member_name':
                aVal = a.member_name.toLowerCase();
                bVal = b.member_name.toLowerCase();
                break;
            case 'active_clients':
                aVal = a.active_clients;
                bVal = b.active_clients;
                break;
            case 'city':
                aVal = a.city.toLowerCase();
                bVal = b.city.toLowerCase();
                break;
            default:
                return 0;
        }
        
        if (aVal < bVal) return isAscending ? -1 : 1;
        if (aVal > bVal) return isAscending ? 1 : -1;
        return 0;
    });
}

/**
 * Display Analytics Data
 */
function displayAnalytics() {
    analyticsTableBody.innerHTML = '';
    
    if (filteredBrokers.length === 0) {
        analyticsTableBody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    No brokers found matching your criteria.
                </td>
            </tr>
        `;
        resultsInfo.classList.add('d-none');
        return;
    }
    
    filteredBrokers.forEach(broker => {
        const row = document.createElement('tr');
        
        // Format website
        let websiteHtml = '-';
        if (broker.website && broker.website !== '-' && broker.website !== 'N/A') {
            const displayUrl = broker.website.length > 30 ? 
                broker.website.substring(0, 30) + '...' : broker.website;
            websiteHtml = `<a href="${escapeHtml(broker.website)}" target="_blank" 
                style="color: var(--primary-color); text-decoration: none;">
                ${escapeHtml(displayUrl)}
            </a>`;
        }
        
        row.innerHTML = `
            <td>${escapeHtml(broker.sr_no || '-')}</td>
            <td>
                <strong class="broker-name-link" onclick="viewDetails('${broker.member_code}')" 
                    style="cursor: pointer; color: #2563eb; text-decoration: none;">
                    ${escapeHtml(broker.member_name || '-')}
                </strong>
            </td>
            <td><strong style="color: var(--primary-color);">${formatNumber(broker.active_clients)}</strong></td>
            <td>${escapeHtml(broker.city || '-')}</td>
            <td>${websiteHtml}</td>
            <td>${escapeHtml(broker.ceo_name || '-')}</td>
            <td>${escapeHtml(broker.compliance_officer || '-')}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="viewDetails('${broker.member_code}')">
                    View Details
                </button>
            </td>
        `;
        
        analyticsTableBody.appendChild(row);
    });
    
    // Update results count
    resultsCount.textContent = formatNumber(filteredBrokers.length);
    resultsInfo.classList.remove('d-none');
    tableContainer.classList.remove('d-none');
}

/**
 * Sort by Column (when clicking header)
 */
function sortByColumn(column) {
    // Toggle sort order if same column
    if (currentSort.by === column) {
        currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.by = column;
        currentSort.order = 'desc';
    }
    
    // Update select elements
    sortBy.value = column;
    sortOrder.value = currentSort.order;
    
    // Apply sorting
    sortBrokers();
    displayAnalytics();
    updateSortIndicators();
}

/**
 * Update Sort Indicators in Table Headers
 */
function updateSortIndicators() {
    // Reset all indicators
    ['sr_no', 'member_name', 'active_clients', 'city'].forEach(col => {
        const indicator = document.getElementById(`sort-${col}`);
        if (indicator) {
            indicator.textContent = '↕️';
        }
    });
    
    // Set active indicator
    const activeIndicator = document.getElementById(`sort-${currentSort.by}`);
    if (activeIndicator) {
        activeIndicator.textContent = currentSort.order === 'asc' ? '↑' : '↓';
    }
}

/**
 * Clear Filters
 */
function clearFilters() {
    searchInput.value = '';
    sortBy.value = 'active_clients';
    sortOrder.value = 'desc';
    currentSort = { by: 'active_clients', order: 'desc' };
    
    console.log('✖️ Filters cleared');
    applyFilters();
}

/**
 * View Broker Details (Navigate to Screen 3)
 */
function viewDetails(memberCode) {
    console.log('📄 Viewing details for:', memberCode);
    window.location.href = `details.html?code=${memberCode}`;
}

/**
 * Show/Hide Loading Spinner
 */
function showLoading(show) {
    if (show) {
        loadingSpinner.classList.remove('d-none');
        tableContainer.classList.add('d-none');
        resultsInfo.classList.add('d-none');
    } else {
        loadingSpinner.classList.add('d-none');
    }
}

/**
 * Show Error Message
 */
function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove('d-none');
    tableContainer.classList.add('d-none');
    resultsInfo.classList.add('d-none');
}

/**
 * Hide Error Message
 */
function hideError() {
    errorMessage.classList.add('d-none');
}

/**
 * Format Number with Commas
 */
function formatNumber(num) {
    if (!num && num !== 0) return '-';
    return parseInt(num).toLocaleString();
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for use in HTML
window.applyFilters = applyFilters;
window.clearFilters = clearFilters;
window.viewDetails = viewDetails;
window.sortByColumn = sortByColumn;

console.log('✅ Analytics Dashboard script loaded');
