/**
 * Broker Dashboard (Screen 1) - JavaScript
 * ========================================
 * Handles broker list display with pagination, search, and filtering
 */

// Configuration
const API_BASE_URL = 'http://192.168.119.183:8755/api/v1';

// State Management
let currentPage = 1;
let currentLimit = 50;
let currentSearch = '';
let currentCity = '';
let currentSort = { by: 'sr_no', order: 'asc' };
let allBrokers = [];
let totalPages = 0;
let totalRecords = 0;

// DOM Elements
const loadingSpinner = document.getElementById('loadingSpinner');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const tableContainer = document.getElementById('tableContainer');
const brokerTableBody = document.getElementById('brokerTableBody');
const paginationContainer = document.getElementById('paginationContainer');
const searchInput = document.getElementById('searchInput');
const cityFilter = document.getElementById('cityFilter');
const limitSelect = document.getElementById('limitSelect');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Broker Dashboard initializing...');
    loadStatistics();
    loadCityFilters();
    loadBrokers();
    
    // Add enter key support for search
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            applyFilters();
        }
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
            document.getElementById('citiesCount').textContent = formatNumber(data.data.cities_count);
            document.getElementById('avgClients').textContent = formatNumber(data.data.avg_active_clients);
            document.getElementById('completionRate').textContent = data.data.completion_percentage + '%';
        }
    } catch (error) {
        console.error('❌ Error loading statistics:', error);
    }
}

/**
 * Load City Filters
 */
async function loadCityFilters() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/filters/cities`);
        const data = await response.json();
        
        if (data.success && data.data) {
            const cities = data.data;
            cityFilter.innerHTML = '<option value="">All Cities</option>';
            
            cities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                cityFilter.appendChild(option);
            });
            
            console.log(`✅ Loaded ${cities.length} cities`);
        }
    } catch (error) {
        console.error('❌ Error loading cities:', error);
    }
}

/**
 * Load Brokers with Pagination
 */
async function loadBrokers() {
    showLoading(true);
    hideError();
    
    try {
        // Build query parameters
        const params = new URLSearchParams({
            page: currentPage,
            limit: currentLimit
        });
        
        if (currentSearch) {
            params.append('search', currentSearch);
        }
        
        if (currentCity) {
            params.append('city', currentCity);
        }
        
        const url = `${API_BASE_URL}/dashboard/brokers?${params}`;
        console.log('📡 Fetching:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success && data.data) {
            allBrokers = data.data.brokers || data.data;
            sortAndDisplayBrokers();
            updatePagination(data.pagination);
            showTable(true);
            console.log(`✅ Loaded ${allBrokers.length} brokers`);
        } else {
            showError(data.error || 'Failed to load brokers');
        }
    } catch (error) {
        console.error('❌ Error loading brokers:', error);
        showError('Failed to connect to server. Please ensure the backend is running.');
    } finally {
        showLoading(false);
    }
}

/**
 * Sort and Display Brokers
 */
function sortAndDisplayBrokers() {
    const isAsc = currentSort.order === 'asc';

    allBrokers.sort((a, b) => {
        let aVal, bVal;

        switch (currentSort.by) {
            case 'sr_no':
                return isAsc
                    ? a.sr_no - b.sr_no
                    : b.sr_no - a.sr_no;

            case 'member_name':
                aVal = (a.member_name || '').trim();
                bVal = (b.member_name || '').trim();

                return isAsc
                    ? aVal.localeCompare(bVal, undefined, {
                          numeric: true,
                          sensitivity: 'base'
                      })
                    : bVal.localeCompare(aVal, undefined, {
                          numeric: true,
                          sensitivity: 'base'
                      });

            default:
                return 0;
        }
    });

    displayBrokers(allBrokers);
    updateSortIndicators();
}


/**
 * Sort by Column (Header Click)
 */
function sortByColumn(column) {
    if (currentSort.by === column) {
        currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.by = column;
        currentSort.order = 'asc'; // same as second code
    }

    sortAndDisplayBrokers();
    console.log(`🔄 Sorted by ${column} (${currentSort.order})`);
}


/**
 * Update Sort Indicators in Table Headers
 */
function updateSortIndicators() {
    ['sr_no', 'member_name'].forEach(col => {
        const indicator = document.getElementById(`sort-${col}`);
        if (indicator) indicator.textContent = '↕️';
    });

    const active = document.getElementById(`sort-${currentSort.by}`);
    if (active) {
        active.textContent = currentSort.order === 'asc' ? '↑' : '↓';
    }
}

/**
 * Display Brokers in Table
 */
function displayBrokers(brokers) {
    brokerTableBody.innerHTML = '';
    
    if (brokers.length === 0) {
        brokerTableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    No brokers found matching your criteria.
                </td>
            </tr>
        `;
        return;
    }
    
    brokers.forEach(broker => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${escapeHtml(broker.sr_no || '-')}</td>
            <td>
                <strong class="broker-name-link" onclick="viewDetails('${broker.member_code}')" style="cursor: pointer; color: #2563eb; text-decoration: none;">
                    ${escapeHtml(broker.member_name || '-')}
                </strong>
            </td>
            <td>${escapeHtml(broker.sebi_reg_no || '-')}</td>
            <td>${escapeHtml(broker.member_code || '-')}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="viewDetails('${broker.member_code}')">
                    View Details
                </button>
            </td>
        `;
        brokerTableBody.appendChild(row);
    });
}

/**
 * Update Pagination Controls
 */
function updatePagination(pagination) {
    if (!pagination) return;
    
    totalPages = pagination.total_pages;
    totalRecords = pagination.total_records;
    currentPage = pagination.current_page;
    
    paginationContainer.innerHTML = '';
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Previous';
    prevBtn.disabled = !pagination.has_prev;
    prevBtn.onclick = () => goToPage(currentPage - 1);
    paginationContainer.appendChild(prevBtn);
    
    // Page info
    const pageInfo = document.createElement('span');
    pageInfo.className = 'pagination-info';
    pageInfo.textContent = `Page ${currentPage} of ${totalPages} (${formatNumber(totalRecords)} total)`;
    paginationContainer.appendChild(pageInfo);
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Next →';
    nextBtn.disabled = !pagination.has_next;
    nextBtn.onclick = () => goToPage(currentPage + 1);
    paginationContainer.appendChild(nextBtn);
    
    // Show pagination
    paginationContainer.classList.remove('d-none');
}

/**
 * Go to Specific Page
 */
function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadBrokers();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Apply Filters
 */
function applyFilters() {
    currentPage = 1; // Reset to first page
    currentSearch = searchInput.value.trim();
    currentCity = cityFilter.value;
    currentLimit = parseInt(limitSelect.value);
    
    console.log('🔍 Applying filters:', { currentSearch, currentCity, currentLimit });
    loadBrokers();
}

/**
 * Clear Filters
 */
function clearFilters() {
    currentPage = 1;
    currentSearch = '';
    currentCity = '';
    currentLimit = 50;
    
    searchInput.value = '';
    cityFilter.value = '';
    limitSelect.value = '50';
    
    console.log('✖️ Filters cleared');
    loadBrokers();
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
        paginationContainer.classList.add('d-none');
    } else {
        loadingSpinner.classList.add('d-none');
    }
}

/**
 * Show/Hide Table
 */
function showTable(show) {
    if (show) {
        tableContainer.classList.remove('d-none');
    } else {
        tableContainer.classList.add('d-none');
    }
}

/**
 * Show Error Message
 */
function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove('d-none');
    tableContainer.classList.add('d-none');
    paginationContainer.classList.add('d-none');
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
window.goToPage = goToPage;
window.sortByColumn = sortByColumn;

console.log('✅ Broker Dashboard script loaded');
