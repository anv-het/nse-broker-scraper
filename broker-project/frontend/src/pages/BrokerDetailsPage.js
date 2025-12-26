// Configuration
const API_BASE_URL = 'http://192.168.119.183:8755/api/v1';

// Get member code from URL
const urlParams = new URLSearchParams(window.location.search);
const memberCode = urlParams.get('code');

// DOM Elements
const loadingSpinner = document.getElementById('loadingSpinner');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const detailsContent = document.getElementById('detailsContent');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (!memberCode) {
        showError('No member code provided. Please go back to the list and select a broker.');
        return;
    }
    
    loadBrokerDetails();
});

// Load Broker Details
async function loadBrokerDetails() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/brokers/${memberCode}`);
        const data = await response.json();
        
        if (data.success && data.data) {
            displayBrokerDetails(data.data);
        } else {
            showError(data.error || 'Failed to load broker details. The broker may not exist in the database.');
        }
    } catch (error) {
        console.error('Error loading broker details:', error);
        showError('Failed to connect to server. Please make sure the API server is running.');
    } finally {
        showLoading(false);
    }
}

// Main Display Function
function displayBrokerDetails(broker) {
    console.log('Broker data received:', broker);
    
    // Section 1: Basic Information
    displayBasicInfo(broker);
    
    // Section 2: Office Addresses
    displayOfficeAddresses(broker);
    
    // Section 3: Segment Status
    displaySegmentStatus(broker);
    
    // Section 4: Other Details
    displayOtherDetails(broker);
    
    // Section 5: Website & Apps
    displayWebsiteApps(broker);
    
    // Section 6: SEBI Details
    displaySebiDetails(broker);
    
    // Section 7: Depository Participant
    displayDepositoryDetails(broker);
    
    // Section 8: Stock Exchange Membership
    displayExchangeMembership(broker);
    
    // Section 9: Key Management
    displayKeyManagement(broker);
    
    // Section 10: Directors
    displayDirectors(broker);
    
    // Section 11: Complaints Data
    displayComplaintsData(broker);
    
    // Section: Disciplinary Actions
    displayDisciplinaryActions(broker);
    
    // Section 12: Associate Companies
    displayAssociateCompanies(broker);
    
    // Section 13: Trading Member Summary
    displayTradingSummary(broker);
    
    // Section 14: Client Bank Accounts
    displayBankAccounts(broker);
    
    // Section 15: Net Worth
    displayNetWorth(broker);
    
    // Section 16: Metadata
    displayMetadata(broker);
    
    // Show content
    detailsContent.style.display = 'block';
}

// ============ Section 1: Basic Information ============
function displayBasicInfo(broker) {
    const basicDetails = broker.Basic_Details || {};
    
    setText('memberName', broker['Member Name'] || basicDetails['Member Name'] || '-');
    setText('sebiRegNo', broker['SEBI Registration no'] || basicDetails['SEBI Registration no'] || '-');
    setText('memberCode', broker['Member Code'] || basicDetails['Member Code'] || '-');
    setText('regDate', basicDetails['SEBI Registration Date'] || '-');
    setText('tradeName', basicDetails['Trade Name'] || '-');
    setText('constitution', basicDetails['Constitution'] || '-');
    setText('yearIncorporation', basicDetails['Year of Incorporation'] || '-');
    setText('yearMembership', basicDetails['Year of NSE Membership'] || '-');
}

// ============ Section 2: Office Addresses ============
function displayOfficeAddresses(broker) {
    // Registered Office
    const regOffice = broker.Registered_Office || {};
    setText('regAddress', regOffice['Registered Office Address'] || '-');
    setText('regCity', regOffice['City'] || '-');
    setText('regPincode', regOffice['Pin Code'] || '-');
    setText('regPhone', regOffice['Phone Number'] || '-');
    setText('regFax', regOffice['Fax Number'] || '-');
    
    const regEmail = regOffice['Email ID'];
    if (regEmail) {
        document.getElementById('regEmail').innerHTML = `<a href="mailto:${regEmail}">${regEmail}</a>`;
    }
    
    // Correspondence Office
    const corrOffice = broker.Correspondence_Office || {};
    setText('corrAddress', corrOffice['Correspondence Office Address'] || '-');
    setText('corrCity', corrOffice['City'] || '-');
    setText('corrPincode', corrOffice['Pin Code'] || '-');
    setText('corrPhone', corrOffice['Phone Number'] || '-');
    setText('corrFax', corrOffice['Fax Number'] || '-');
    
    const corrEmail = corrOffice['Email ID'];
    if (corrEmail) {
        document.getElementById('corrEmail').innerHTML = `<a href="mailto:${corrEmail}">${corrEmail}</a>`;
    }
}

// ============ Section 3: Segment Status ============
function displaySegmentStatus(broker) {
    const segmentStatus = broker.Segment_Status || {};
    const tableData = segmentStatus.Table_Data || [];
    
    // Show legend
    if (segmentStatus.LEGEND) {
        document.getElementById('segmentLegend').textContent = segmentStatus.LEGEND;
    }
    
    const tbody = document.getElementById('segmentTableBody');
    tbody.innerHTML = '';
    
    if (tableData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="no-data">No segment data available</td></tr>';
        return;
    }
    
    // Display segments directly from the table data
    tableData.forEach((segment, index) => {
        const srNo = segment['Sr no'] || (index + 1);
        const segmentName = segment['Segment'] || '-';
        const status = segment['Status'] || 'Unknown';
        
        const row = document.createElement('tr');
        const statusClass = status === 'Enabled' ? 'status-enabled' : 
                          status === 'Disabled' ? 'status-disabled' : 'status-notenabled';
        row.innerHTML = `
            <td>${srNo}</td>
            <td>${segmentName}</td>
            <td><span class="status-badge ${statusClass}">${status}</span></td>
        `;
        tbody.appendChild(row);
    });
}

// ============ Section 4: Other Details ============
function displayOtherDetails(broker) {
    const outerDetails = broker.Outer_Details || {};
    
    // AP List
    const apList = outerDetails['List of APs registered'];
    if (apList && apList.text) {
        document.getElementById('apList').innerHTML = `<a href="#" class="info-link">${apList.text}</a>`;
    }
    
    // Dealing Offices
    const dealingOffices = outerDetails['List of dealing offices'];
    if (dealingOffices && dealingOffices.text) {
        document.getElementById('dealingOffices').innerHTML = `<a href="#" class="info-link">${dealingOffices.text}</a>`;
    }
    
    setText('isListed', outerDetails['Listed'] || '-');
    setText('grievanceEmail', outerDetails['Investor Grievance Email ID'] || '-');
    setText('clientTypes', outerDetails['Types of Clients Served'] || '-');
}

// ============ Section 5: Website & Apps ============
function displayWebsiteApps(broker) {
    const websiteApp = broker.website_app || {};
    
    // Website
    const website = websiteApp['Website Address'];
    if (website) {
        document.getElementById('websiteAddress').innerHTML = `<a href="${website}" target="_blank" class="website-url">${website}</a>`;
    }
    
    // Apps
    const apps = websiteApp.Apps || [];
    const appsBody = document.getElementById('appsTableBody');
    appsBody.innerHTML = '';
    
    const parsedApps = parseApps(apps);
    if (parsedApps.length > 0) {
        parsedApps.forEach(app => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${app.srNo}</td>
                <td>${app.name}</td>
                <td>${app.playStore ? `<a href="${app.playStore}" target="_blank">📱 Play Store</a>` : '-'}</td>
                <td>${app.appStore ? `<a href="${app.appStore}" target="_blank">🍎 App Store</a>` : '-'}</td>
            `;
            appsBody.appendChild(row);
        });
    } else {
        appsBody.innerHTML = '<tr><td colspan="4" class="no-data">No app data available</td></tr>';
    }
    
    // Social Media
    const socialMedia = websiteApp['Social Media Details'] || [];
    const socialBody = document.getElementById('socialMediaTableBody');
    socialBody.innerHTML = '';
    
    const parsedSocial = parseSocialMedia(socialMedia);
    if (parsedSocial.length > 0) {
        parsedSocial.forEach(social => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${social.srNo}</td>
                <td>${social.platform}</td>
                <td>${social.handle}</td>
            `;
            socialBody.appendChild(row);
        });
    } else {
        socialBody.innerHTML = '<tr><td colspan="3" class="no-data">No social media data available</td></tr>';
    }
}

function parseApps(apps) {
    const result = [];
    apps.forEach(app => {
        // Support both proper field names and Column_X format
        const srNo = app['Sr.No.'] || app.Column_1;
        const name = app['Name of Mobile Application'] || app.Column_2;
        const playStore = app['Link for Play Store'] || app.Column_3 || '';
        const appStore = app['Link for App Store'] || app.Column_4 || '';
        
        if (srNo && name) {
            result.push({
                srNo: srNo,
                name: name,
                playStore: playStore,
                appStore: appStore
            });
        }
    });
    return result;
}

function parseSocialMedia(socialMedia) {
    const result = [];
    socialMedia.forEach(item => {
        // Support both proper field names and Column_X format
        const srNo = item['Sr.No.'] || item.Column_1;
        const platform = item['Name of social media'] || item.Column_2;
        const link = item['Link for social media'] || item.Column_3;
        
        if (srNo && platform && link && link !== 'NA') {
            result.push({
                srNo: srNo,
                platform: platform,
                handle: link
            });
        }
    });
    return result;
}

// ============ Section 6: SEBI Details ============
function displaySebiDetails(broker) {
    const sebiDetails = broker.sebi_details || {};
    const container = document.getElementById('sebiCardsContainer');
    container.innerHTML = '';
    
    const sebiTypes = [
        { key: 'PMS SEBI Registration details', title: 'PMS Registration' },
        { key: 'Research Analysts details', title: 'Research Analysts' },
        { key: 'Investment Adviser details', title: 'Investment Adviser' },
        { key: 'Merchant Banker', title: 'Merchant Banker' }
    ];
    
    sebiTypes.forEach(type => {
        const detail = sebiDetails[type.key];
        if (detail) {
            const card = document.createElement('div');
            card.className = 'sebi-card';
            card.innerHTML = `
                <h4>${type.title}</h4>
                <p><strong>Website:</strong> <a href="${detail.Website}" target="_blank">SEBI Portal</a></p>
                <p class="sebi-path"><strong>Path:</strong> ${detail.Path || '-'}</p>
            `;
            container.appendChild(card);
        }
    });
    
    if (container.children.length === 0) {
        container.innerHTML = '<p class="no-data">No SEBI registration details available</p>';
    }
}

// ============ Section 7: Depository Participant ============
function displayDepositoryDetails(broker) {
    const depository = broker.depository_participant_details || {};
    
    if (depository.As_on_Date) {
        document.getElementById('depositoryDate').textContent = `As on ${depository.As_on_Date}`;
    }
    
    const depositories = depository.Depositories || [];
    const tbody = document.getElementById('depositoryTableBody');
    tbody.innerHTML = '';
    
    const parsed = parseDepositories(depositories);
    if (parsed.length > 0) {
        parsed.forEach(dep => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${dep.srNo}</td>
                <td>${dep.name}</td>
                <td>${dep.regNo}</td>
                <td>${dep.link ? `<a href="${dep.link}" target="_blank">View</a>` : '-'}</td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML = '<tr><td colspan="4" class="no-data">No depository data available</td></tr>';
    }
}

function parseDepositories(depositories) {
    const result = [];
    depositories.forEach(item => {
        // Support both proper field names and Column_X format
        const srNo = item['Sr_No'] || item.Column_1;
        const name = item['Name_of_Depository'] || item.Column_2;
        const regNo = item['Registration_No'] || item.Column_3 || '-';
        const link = item['Link'] || item.Column_4 || '';
        
        if (srNo && name) {
            result.push({
                srNo: srNo,
                name: name,
                regNo: regNo,
                link: link
            });
        }
    });
    return result;
}

// ============ Section 8: Stock Exchange Membership ============
function displayExchangeMembership(broker) {
    const exchangeDetails = broker.stock_exchange_membership_details || {};
    
    if (exchangeDetails.As_on_Date) {
        document.getElementById('exchangeDate').textContent = `As on ${exchangeDetails.As_on_Date}`;
    }
    
    const memberships = exchangeDetails.Membership_Details || [];
    const tbody = document.getElementById('exchangeTableBody');
    tbody.innerHTML = '';
    
    const parsed = parseExchangeMembership(memberships);
    if (parsed.length > 0) {
        parsed.forEach(ex => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ex.srNo}</td>
                <td>${ex.name}</td>
                <td>${ex.link ? `<a href="${ex.link}" target="_blank">View</a>` : '-'}</td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML = '<tr><td colspan="3" class="no-data">No exchange membership data available</td></tr>';
    }
}

function parseExchangeMembership(memberships) {
    const result = [];
    memberships.forEach(item => {
        // Support both proper field names and Column_X format
        const srNo = item['Sr.No.'] || item.Column_1;
        const name = item['Name of the Exchange'] || item.Column_2;
        const link = item['Link for the Members'] || item.Column_3 || '';
        
        if (srNo && name) {
            result.push({
                srNo: srNo,
                name: name,
                link: link
            });
        }
    });
    return result;
}

// ============ Section 9: Key Management ============
function displayKeyManagement(broker) {
    const management = broker.key_management_details || {};
    
    const ceo = management.Managing_Director_CEO || {};
    setText('ceoName', ceo.Name || '-');
    setText('ceoDesignation', ceo.Designation || '-');
    
    const compliance = management.Compliance_Officer || {};
    setText('complianceName', compliance.Name || '-');
    setText('complianceEmail', compliance.Email || '-');
    setText('complianceContact', compliance.Contact_Number || '-');
}

// ============ Section 10: Directors ============
function displayDirectors(broker) {
    const directorsDetails = broker.directors_details || {};
    
    if (directorsDetails.As_on_Date) {
        document.getElementById('directorsDate').textContent = `As on ${directorsDetails.As_on_Date}`;
    }
    
    const directors = directorsDetails.Directors || [];
    const tbody = document.getElementById('directorsTableBody');
    tbody.innerHTML = '';
    
    const parsed = parseDirectors(directors);
    if (parsed.length > 0) {
        parsed.forEach(dir => {
            const row = document.createElement('tr');
            const isDesignated = dir.designated === 'Y';
            row.innerHTML = `
                <td>${dir.srNo}</td>
                <td>${dir.name}</td>
                <td><span class="status-badge ${isDesignated ? 'status-enabled' : 'status-disabled'}">${dir.designated}</span></td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML = '<tr><td colspan="3" class="no-data">No director data available</td></tr>';
    }
}

function parseDirectors(directors) {
    const result = [];
    directors.forEach(item => {
        // Support proper field names
        const srNo = item['Sr.No.'];
        const directorName = item['Director Name'];
        const designated = item['Designated Director'];
        
        if (srNo && directorName && designated) {
            result.push({
                srNo: srNo,
                name: directorName,
                designated: designated
            });
        }
    });
    return result;
}

// ============ Section 11: Complaints Data ============
function displayComplaintsData(broker) {
    // SCORES 2.0
    const scores = broker.scores_2_0_complaints || {};
    displayMonthlyData('scoresTableBody', scores.Monthly_Data);
    
    // ODR Complaints
    const odrComplaints = broker.odr_complaints_summary || {};
    displayMonthlyData('odrComplaintsTableBody', odrComplaints.Monthly_Data);
    
    // ODR Arbitration
    const odrArbitration = broker.odr_arbitration_summary || {};
    displayMonthlyData('odrArbitrationTableBody', odrArbitration.Monthly_Data);
    
    // GRC
    const grc = broker.grc_complaints_closed || {};
    if (grc.Note) {
        document.getElementById('grcNote').textContent = grc.Note;
    }
    displayYearlyData('grcTableBody', grc.Yearly_Data);
}


function displayMonthlyData(tbodyId, monthlyData) {
    const tbody = document.getElementById(tbodyId);
    tbody.innerHTML = '';

    if (!monthlyData || Object.keys(monthlyData).length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="no-data">No data available</td>
            </tr>`;
        return;
    }

    // Sort months (latest first)
    const sortedMonths = Object.keys(monthlyData).sort((a, b) => {
        return new Date(b.replace('_', ' ')) - new Date(a.replace('_', ' '));
    });

    sortedMonths.forEach(monthKey => {
        const data = monthlyData[monthKey];

        const formattedMonth = monthKey.replace('_', ' ');

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formattedMonth}</td>
            <td>${data.Opening_Complaints ?? 0}</td>
            <td>${data.Received ?? 0}</td>
        `;
        tbody.appendChild(row);
    });
}

function displayYearlyData(tbodyId, yearlyData) {
    const tbody = document.getElementById(tbodyId);
    tbody.innerHTML = '';

    if (!yearlyData || Object.keys(yearlyData).length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" class="no-data">No data available</td></tr>';
        return;
    }

    Object.entries(yearlyData).forEach(([year, value]) => {
        const row = document.createElement('tr');
        const formattedYear = year.replace('_', ' '); // Year 1, Year 2

        row.innerHTML = `
            <td>${formattedYear}</td>
            <td>${value}</td>
        `;
        tbody.appendChild(row);
    });
}

// ============ Section: Disciplinary Actions ============
function displayDisciplinaryActions(broker) {
    const disciplinary = broker.disciplinary_actions_master || {};
    const container = document.getElementById('disciplinaryContent');
    container.innerHTML = '';
    
    if (disciplinary.As_on_Date) {
        document.getElementById('disciplinaryDate').textContent = `As on ${disciplinary.As_on_Date}`;
    }
    
    // NSE Disciplinary Actions
    if (disciplinary.NSE_Disciplinary_Actions) {
        const section = createDisciplinarySection('NSE Disciplinary Actions', disciplinary.NSE_Disciplinary_Actions);
        container.appendChild(section);
    }
    
    // NSE Member Committee Orders
    if (disciplinary.NSE_Member_Committee_Orders) {
        const section = createDisciplinarySection('NSE Member Committee Orders', disciplinary.NSE_Member_Committee_Orders);
        container.appendChild(section);
    }
    
    // SEBI Orders
    if (disciplinary.SEBI_Orders) {
        const section = createDisciplinarySection('SEBI Orders', disciplinary.SEBI_Orders);
        container.appendChild(section);
    }
    
    // Disclaimer
    if (disciplinary.Disclaimer && disciplinary.Disclaimer.length > 0) {
        const disclaimer = document.createElement('div');
        disclaimer.className = 'disclaimer-box';
        disclaimer.innerHTML = `<p><strong>Disclaimer:</strong> ${disciplinary.Disclaimer.join(' ')}</p>`;
        container.appendChild(disclaimer);
    }
    
    if (container.children.length === 0) {
        container.innerHTML = '<p class="no-data">No disciplinary action data available</p>';
    }
}

function createDisciplinarySection(title, data) {
    const section = document.createElement('div');
    section.className = 'disciplinary-subsection';
    section.innerHTML = `<h4 class="disciplinary-title">${title}</h4>`;
    
    // Display penalty data if available
    const yearData = data.year_2021_2022 || data.year_2022_2023 || {};
    if (yearData.Total_Monetary_Penalty_In_Rs) {
        const penaltyTable = document.createElement('table');
        penaltyTable.className = 'data-table';
        penaltyTable.innerHTML = `
            <thead>
                <tr>
                    <th>Year</th>
                    <th>Total Monetary Penalty (Rs.)</th>
                </tr>
            </thead>
            <tbody>
                ${Object.entries(yearData.Total_Monetary_Penalty_In_Rs).map(([year, amount]) => `
                    <tr>
                        <td>${year}</td>
                        <td>₹ ${amount}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        section.appendChild(penaltyTable);
    }
    
    return section;
}


// ============ Section 12: Associate Companies ============
function cleanText(text) {
    if (!text) return '';
    const el = document.createElement('textarea');
    el.innerHTML = text;
    return el.value.trim();
}

function displayAssociateCompanies(broker) {
    const associate = broker.associate_companies || {};

    // ✅ Correct ID
    if (associate.As_on_Date) {
        document.getElementById('associateCompaniesNote').textContent =
            `As on ${associate.As_on_Date}`;
    }

    const companies = associate.Companies || [];
    const tbody = document.getElementById('associateCompaniesTableBody');
    tbody.innerHTML = '';

    const parsed = parseAssociateCompanies(companies);

    if (parsed.length > 0) {
        parsed.forEach(company => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${company.srNo}</td>
                <td>${company.name}</td>
                <td>${company.sector}</td>
                <td class="small-text monospace">${company.sebiReg}</td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML =
            '<tr><td colspan="4" class="no-data">No associate company data available</td></tr>';
    }
}

function parseAssociateCompanies(companies) {
    const result = [];

    if (!Array.isArray(companies)) return result;

    companies.forEach(item => {
        const srNo = item['Sr no'];
        const companyName = item['Name of the Company'];
        const sector = item['Financial Market Sector'];
        const sebiReg = cleanText(item['SEBI Registration Number, if any']);

        if (srNo && companyName) {
            result.push({
                srNo,
                name: cleanText(companyName),
                sector: sector || '-',
                sebiReg: sebiReg || '-'
            });
        }
    });

    return result;
}


// ============ Section 13: Trading Member Summary ============
function displayTradingSummary(broker) {
    const tradingSummary = broker.summary_trading_member_info || {};
    
    if (tradingSummary.Reporting_Period) {
        document.getElementById('tradingSummaryPeriod').textContent = `Reporting Period: ${tradingSummary.Reporting_Period}`;
    }
    
    const periodData = tradingSummary.Data_By_Period || {};
    const tbody = document.getElementById('tradingSummaryTableBody');
    tbody.innerHTML = '';
    
    if (Object.keys(periodData).length > 0) {
        Object.entries(periodData).forEach(([period, data]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${period}</strong></td>
                <td>${data.Number_of_branches_of_TM || '-'}</td>
                <td>${data.Number_of_employees_of_TM || '-'}</td>
                <td>${data.Number_of_APs_affiliates_registered_with_Exchanges || '-'}</td>
                <td>${data.Total_number_of_active_clients || '-'}</td>
                <td>${data.Clients_Equity_Cash_Segment || '-'}</td>
                <td>${data.Clients_Derivatives || '-'}</td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">No trading summary data available</td></tr>';
    }
}

// ============ Section 14: Client Bank Accounts ============

function parseBankAccounts(accounts) {
    const result = [];

    if (!Array.isArray(accounts) || accounts.length === 0) {
        return result;
    }

    accounts.forEach(item => {
        const srNo = item['Sr no'];
        const name = item['Account Name'];
        const accountNo = item['Account Number'];
        const ifsc = item['IFSC Code'];
        const purpose = item['Account Purpose'];

        if (srNo && name && accountNo) {
            result.push({
                srNo: srNo,
                name: name,
                accountNo: accountNo,
                ifsc: ifsc || '-',
                purpose: purpose || '-'
            });
        }
    });

    return result;
}

function displayBankAccounts(broker) {
    const bankAccounts = broker.client_bank_accounts || {};

    if (bankAccounts.Note) {
        document.getElementById('bankAccountsNote').textContent = bankAccounts.Note;
    }

    const tbody = document.getElementById('bankAccountsTableBody');
    tbody.innerHTML = '';

    const parsed = parseBankAccounts(bankAccounts.Accounts || []);

    if (parsed.length > 0) {
        parsed.forEach(acc => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${acc.srNo}</td>
                <td>${acc.name}</td>
                <td class="monospace">${acc.accountNo}</td>
                <td class="monospace">${acc.ifsc}</td>
                <td>${acc.purpose}</td>
            `;
            tbody.appendChild(row);
        });
    } else {
        tbody.innerHTML =
            '<tr><td colspan="5" class="no-data">No bank account data available</td></tr>';
    }
}

// ============ Section 15: Net Worth ============
function displayNetWorth(broker) {
    const netWorth = broker.trading_member_net_worth || {};
    
    setText('networthDate', netWorth.As_on_Date || '-');
    setText('networthAmount', netWorth.Net_Worth_Rs !== undefined ? `₹ ${netWorth.Net_Worth_Rs.toLocaleString()}` : '-');
    setText('networthRef', netWorth.Regulation_Reference || '-');
}

// ============ Section 16: Metadata ============
function displayMetadata(broker) {
    const metadata = broker._metadata || {};
    
    setText('metaSrNo', metadata.sr_no || '-');
    setText('metaVersion', metadata.scraper_version || '-');
    
    if (metadata.scraped_at) {
        const date = new Date(metadata.scraped_at);
        setText('metaScrapedAt', date.toLocaleString());
    }
    
    if (metadata.details_url) {
        document.getElementById('metaUrl').innerHTML = `<a href="${metadata.details_url}" target="_blank">View on NSE</a>`;
    }
}

// ============ Helper Functions ============
function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value || '-';
    }
}

function showLoading(show) {
    loadingSpinner.style.display = show ? 'flex' : 'none';
    detailsContent.style.display = show ? 'none' : 'block';
    errorMessage.style.display = 'none';
}

function showError(message) {
    loadingSpinner.style.display = 'none';
    detailsContent.style.display = 'none';
    errorMessage.style.display = 'block';
    errorText.textContent = message;
}
