// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State
let currentPage = 1;
let totalPages = 1;
let currentFilters = {
    search: '',
    state: '',
    city: ''
};

// DOM Elements
const searchInput = document.getElementById('searchInput');
const stateFilter = document.getElementById('stateFilter');
const cityFilter = document.getElementById('cityFilter');
const clearFiltersBtn = document.getElementById('clearFilters');
const brokerTableBody = document.getElementById('brokerTableBody');
const loadingSpinner = document.getElementById('loadingSpinner');
const tableContainer = document.getElementById('tableContainer');
const paginationDiv = document.getElementById('pagination');
const currentPageSpan = document.getElementById('currentPage');
const totalPagesSpan = document.getElementById('totalPages');
const totalRecordsSpan = document.getElementById('totalRecords');
const firstPageBtn = document.getElementById('firstPage');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const lastPageBtn = document.getElementById('lastPage');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadFilterOptions();
    loadBrokers();
    
    // Event listeners
    searchInput.addEventListener('input', debounce(() => {
        currentFilters.search = searchInput.value;
        currentPage = 1;
        loadBrokers();
    }, 500));
    
    stateFilter.addEventListener('change', () => {
        currentFilters.state = stateFilter.value;
        currentPage = 1;
        loadBrokers();
    });
    
    cityFilter.addEventListener('change', () => {
        currentFilters.city = cityFilter.value;
        currentPage = 1;
        loadBrokers();
    });
    
    clearFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        stateFilter.value = '';
        cityFilter.value = '';
        currentFilters = { search: '', state: '', city: '' };
        currentPage = 1;
        loadBrokers();
    });
    
    firstPageBtn.addEventListener('click', () => {
        currentPage = 1;
        loadBrokers();
    });
    
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadBrokers();
        }
    });
    
    nextPageBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadBrokers();
        }
    });
    
    lastPageBtn.addEventListener('click', () => {
        currentPage = totalPages;
        loadBrokers();
    });
});

// Load Statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalBrokers').textContent = data.data.total_brokers;
            document.getElementById('detailedBrokers').textContent = data.data.detailed_brokers;
            document.getElementById('completionRate').textContent = data.data.completion_percentage + '%';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load Filter Options
async function loadFilterOptions() {
    try {
        // Load states
        const statesResponse = await fetch(`${API_BASE_URL}/filters/states`);
        const statesData = await statesResponse.json();
        
        if (statesData.success) {
            statesData.data.forEach(state => {
                const option = document.createElement('option');
                option.value = state;
                option.textContent = state;
                stateFilter.appendChild(option);
            });
        }
        
        // Load cities
        const citiesResponse = await fetch(`${API_BASE_URL}/filters/cities`);
        const citiesData = await citiesResponse.json();
        
        if (citiesData.success) {
            citiesData.data.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                cityFilter.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}

// Load Brokers
async function loadBrokers() {
    showLoading(true);
    
    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: 50,
            search: currentFilters.search,
            state: currentFilters.state,
            city: currentFilters.city
        });
        
        const response = await fetch(`${API_BASE_URL}/brokers?${params}`);
        const data = await response.json();
        
        if (data.success) {
            displayBrokers(data.data);
            updatePagination(data.pagination);
        } else {
            showError('Failed to load broker data');
        }
    } catch (error) {
        console.error('Error loading brokers:', error);
        showError('Failed to connect to server. Please make sure the API server is running.');
    } finally {
        showLoading(false);
    }
}

// Display Brokers
function displayBrokers(brokers) {
    brokerTableBody.innerHTML = '';
    
    if (brokers.length === 0) {
        brokerTableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #6c757d;">
                    No brokers found matching your criteria
                </td>
            </tr>
        `;
        return;
    }
    
    brokers.forEach(broker => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${broker.sr_no || '-'}</td>
            <td>
                <span class="broker-name" onclick="viewDetails('${broker.member_code}')">
                    ${broker.member_name || '-'}
                </span>
            </td>
            <td>${broker.sebi_reg_no || '-'}</td>
            <td>${broker.member_code || '-'}</td>
            <td>
                <button class="btn-view" onclick="viewDetails('${broker.member_code}')">
                    View Details
                </button>
            </td>
        `;
        brokerTableBody.appendChild(row);
    });
}

// Update Pagination
function updatePagination(pagination) {
    totalPages = pagination.total_pages;
    currentPage = pagination.current_page;
    
    currentPageSpan.textContent = currentPage;
    totalPagesSpan.textContent = totalPages;
    totalRecordsSpan.textContent = pagination.total_records;
    
    firstPageBtn.disabled = !pagination.has_prev;
    prevPageBtn.disabled = !pagination.has_prev;
    nextPageBtn.disabled = !pagination.has_next;
    lastPageBtn.disabled = !pagination.has_next;
}

// View Details
function viewDetails(memberCode) {
    window.location.href = `details.html?code=${memberCode}`;
}

// Show Loading
function showLoading(show) {
    if (show) {
        loadingSpinner.style.display = 'flex';
        tableContainer.style.display = 'none';
        paginationDiv.style.display = 'none';
    } else {
        loadingSpinner.style.display = 'none';
        tableContainer.style.display = 'block';
        paginationDiv.style.display = 'flex';
    }
}

// Show Error
function showError(message) {
    brokerTableBody.innerHTML = `
        <tr>
            <td colspan="5" style="text-align: center; padding: 40px; color: #dc3545;">
                ⚠️ ${message}
            </td>
        </tr>
    `;
}

// Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
