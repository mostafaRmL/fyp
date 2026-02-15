/**
 * Medical Assistant - Frontend JavaScript
 * 
 * Handles user interactions and API communication
 */

// API Configuration
const API_BASE_URL = window.location.origin;
const API_ENDPOINT = `${API_BASE_URL}/api/analyze`;

// DOM Elements
const symptomForm = document.getElementById('symptomForm');
const symptomsInput = document.getElementById('symptomsInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnText = analyzeBtn.querySelector('.btn-text');
const btnLoading = analyzeBtn.querySelector('.btn-loading');
const charCount = document.getElementById('charCount');

const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Character counter
symptomsInput.addEventListener('input', () => {
    const length = symptomsInput.value.length;
    charCount.textContent = `${length} / 1000`;
    
    if (length > 900) {
        charCount.style.color = 'var(--danger-color)';
    } else {
        charCount.style.color = 'var(--text-tertiary)';
    }
});

// Form submission
symptomForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const symptoms = symptomsInput.value.trim();
    
    if (!symptoms || symptoms.length < 3) {
        showError('Please enter at least 3 characters to describe your symptoms.');
        return;
    }
    
    // Analyze symptoms
    await analyzeSymptoms(symptoms);
});

/**
 * Analyze symptoms via API
 */
async function analyzeSymptoms(symptoms) {
    // Show loading state
    setLoadingState(true);
    hideError();
    hideResults();
    
    try {
        console.log('Sending request to:', API_ENDPOINT);
        
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symptoms })
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to analyze symptoms');
        }
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to analyze symptoms. Please try again.');
    } finally {
        setLoadingState(false);
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    // User symptoms
    document.getElementById('userSymptoms').textContent = data.user_symptoms;
    
    if (data.analysis) {
        // Conditions
        const conditionsContainer = document.getElementById('conditions');
        conditionsContainer.innerHTML = '';
        
        if (data.analysis.identified_conditions && data.analysis.identified_conditions.length > 0) {
            data.analysis.identified_conditions.forEach(condition => {
                const tag = document.createElement('span');
                tag.className = 'condition-tag';
                tag.textContent = condition;
                conditionsContainer.appendChild(tag);
            });
        } else {
            conditionsContainer.textContent = 'No specific conditions identified';
        }
        
        // Confidence
        const confidenceBadge = document.getElementById('confidence');
        const confidence = data.analysis.confidence || 'medium';
        confidenceBadge.className = `confidence-badge confidence-${confidence}`;
        confidenceBadge.textContent = confidence;
        
        // Reasoning
        document.getElementById('reasoning').textContent = data.analysis.reasoning || 'No reasoning provided';
    }
    
    // Medicines
    const medicinesContainer = document.getElementById('medicinesList');
    const medicineCount = document.getElementById('medicineCount');
    
    medicinesContainer.innerHTML = '';
    
    if (data.recommended_medicines && data.recommended_medicines.length > 0) {
        medicineCount.textContent = `Found ${data.recommended_medicines.length} medicine(s)`;
        
        data.recommended_medicines.forEach(medicine => {
            const card = createMedicineCard(medicine);
            medicinesContainer.appendChild(card);
        });
    } else {
        medicineCount.textContent = 'No medicines found';
        medicinesContainer.innerHTML = '<p style="color: var(--text-secondary);">No medicines found in the database for the identified conditions. Please consult a healthcare professional.</p>';
    }
    
    // Disclaimer
    document.getElementById('disclaimer').textContent = data.disclaimer;
    
    // Show results
    showResults();
}

/**
 * Create medicine card element
 */
function createMedicineCard(medicine) {
    const card = document.createElement('div');
    card.className = 'medicine-card';
    
    // Header
    const header = document.createElement('div');
    header.className = 'medicine-header';
    
    const nameDiv = document.createElement('div');
    const name = document.createElement('div');
    name.className = 'medicine-name';
    name.textContent = medicine.name || 'Unknown';
    nameDiv.appendChild(name);
    
    const id = document.createElement('div');
    id.className = 'medicine-id';
    id.textContent = medicine.drug_id || '';
    nameDiv.appendChild(id);
    
    header.appendChild(nameDiv);
    card.appendChild(header);
    
    // Description
    if (medicine.description) {
        const desc = document.createElement('div');
        desc.className = 'medicine-description';
        desc.textContent = medicine.description;
        card.appendChild(desc);
    }
    
    // Details
    const details = document.createElement('div');
    details.className = 'medicine-details';
    
    if (medicine.chemical_formula) {
        details.appendChild(createDetailRow('Chemical Formula:', medicine.chemical_formula));
    }
    
    if (medicine.molecular_mass) {
        details.appendChild(createDetailRow('Molecular Mass:', medicine.molecular_mass));
    }
    
    if (medicine.atc_code) {
        details.appendChild(createDetailRow('ATC Code:', medicine.atc_code));
    }
    
    if (medicine.medical_conditions && medicine.medical_conditions.length > 0) {
        const conditionsRow = document.createElement('div');
        conditionsRow.className = 'medicine-detail';
        
        const label = document.createElement('div');
        label.className = 'detail-label';
        label.textContent = 'Treats:';
        
        const conditionsContainer = document.createElement('div');
        conditionsContainer.className = 'medicine-conditions';
        
        medicine.medical_conditions.forEach(condition => {
            const tag = document.createElement('span');
            tag.className = 'medicine-condition-tag';
            tag.textContent = condition;
            conditionsContainer.appendChild(tag);
        });
        
        conditionsRow.appendChild(label);
        conditionsRow.appendChild(conditionsContainer);
        details.appendChild(conditionsRow);
    }
    
    if (details.children.length > 0) {
        card.appendChild(details);
    }
    
    return card;
}

/**
 * Create detail row
 */
function createDetailRow(label, value) {
    const row = document.createElement('div');
    row.className = 'medicine-detail';
    
    const labelDiv = document.createElement('div');
    labelDiv.className = 'detail-label';
    labelDiv.textContent = label;
    
    const valueDiv = document.createElement('div');
    valueDiv.className = 'detail-value';
    valueDiv.textContent = value;
    
    row.appendChild(labelDiv);
    row.appendChild(valueDiv);
    
    return row;
}

/**
 * Set loading state
 */
function setLoadingState(isLoading) {
    if (isLoading) {
        analyzeBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
    } else {
        analyzeBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
}

/**
 * Show results section
 */
function showResults() {
    resultsSection.style.display = 'block';
    
    // Smooth scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

/**
 * Hide results section
 */
function hideResults() {
    resultsSection.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    errorSection.style.display = 'block';
    
    // Smooth scroll to error
    setTimeout(() => {
        errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

/**
 * Hide error message
 */
function hideError() {
    errorSection.style.display = 'none';
}

/**
 * Initialize app
 */
function init() {
    console.log('Medical Assistant initialized');
    console.log('API Endpoint:', API_ENDPOINT);
    
    // Focus on input
    symptomsInput.focus();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}