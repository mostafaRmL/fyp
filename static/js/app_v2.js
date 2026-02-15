/**
 * Medical Assistant v2.0 - Frontend JavaScript
 * Ontology-Based Similarity Search
 * 
 * Handles V2 API interactions for symptom and disease-based drug search
 */

// API Configuration
const API_BASE_URL = window.location.origin;
const API_V2_BASE = `${API_BASE_URL}/api/v2`;

// DOM Elements
const symptomForm = document.getElementById('symptomForm');
const diseaseForm = document.getElementById('diseaseForm');
const symptomSearchBtn = document.getElementById('symptomSearchBtn');
const diseaseSearchBtn = document.getElementById('diseaseSearchBtn');

const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Current active mode
let currentMode = 'symptom';

/**
 * Switch between symptom and disease modes
 */
function switchMode(mode) {
    currentMode = mode;
    
    // Update tabs
    document.querySelectorAll('.mode-tab').forEach(tab => {
        if (tab.dataset.mode === mode) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    // Update mode sections
    document.querySelectorAll('.search-mode').forEach(section => {
        if (section.id === `${mode}Mode`) {
            section.classList.add('active');
        } else {
            section.classList.remove('active');
        }
    });
    
    // Hide results and errors
    hideResults();
    hideError();
}

/**
 * Add symptom input field
 */
function addSymptomInput() {
    const container = document.getElementById('symptomInputs');
    const inputRow = document.createElement('div');
    inputRow.className = 'symptom-input-row';
    inputRow.innerHTML = `
        <input type="text" class="form-input symptom-field" placeholder="e.g., headache" required>
        <button type="button" class="btn-icon btn-remove" onclick="removeSymptomInput(this)" title="Remove">✕</button>
    `;
    container.appendChild(inputRow);
}

/**
 * Remove symptom input field
 */
function removeSymptomInput(button) {
    const container = document.getElementById('symptomInputs');
    // Keep at least one input
    if (container.children.length > 1) {
        button.parentElement.remove();
    }
}

/**
 * Get symptoms from input fields
 */
function getSymptoms() {
    const fields = document.querySelectorAll('.symptom-field');
    const symptoms = [];
    
    fields.forEach(field => {
        const value = field.value.trim();
        if (value) {
            symptoms.push(value);
        }
    });
    
    return symptoms;
}

// Symptom Form Submission
symptomForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const symptoms = getSymptoms();
    
    if (symptoms.length === 0) {
        showError('Please enter at least one symptom');
        return;
    }
    
    const topK = parseInt(document.getElementById('symptomTopK').value);
    const minSimilarity = parseFloat(document.getElementById('symptomThreshold').value);
    
    await searchBySymptom(symptoms, topK, minSimilarity);
});

// Disease Form Submission
diseaseForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const diseaseName = document.getElementById('diseaseName').value.trim();
    const diseaseId = document.getElementById('diseaseId').value.trim() || null;
    
    if (!diseaseName) {
        showError('Please enter a disease name');
        return;
    }
    
    const topK = parseInt(document.getElementById('diseaseTopK').value);
    const minSimilarity = parseFloat(document.getElementById('diseaseThreshold').value);
    
    await searchByDisease(diseaseName, diseaseId, topK, minSimilarity);
});

/**
 * Search drugs by symptoms
 */
async function searchBySymptom(symptoms, topK, minSimilarity) {
    setLoadingState(symptomSearchBtn, true);
    hideError();
    hideResults();
    
    try {
        console.log('Searching by symptoms:', symptoms);
        
        const response = await fetch(`${API_V2_BASE}/search/symptom`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symptoms: symptoms,
                top_k: topK,
                min_similarity: minSimilarity
            })
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!data.success) {
            throw new Error(data.message || 'Search failed');
        }
        
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to search drugs. Please try again.');
    } finally {
        setLoadingState(symptomSearchBtn, false);
    }
}

/**
 * Search drugs by disease
 */
async function searchByDisease(diseaseName, diseaseId, topK, minSimilarity) {
    setLoadingState(diseaseSearchBtn, true);
    hideError();
    hideResults();
    
    try {
        console.log('Searching by disease:', diseaseName, diseaseId);
        
        const payload = {
            disease_name: diseaseName,
            top_k: topK,
            min_similarity: minSimilarity
        };
        
        if (diseaseId) {
            payload.disease_id = diseaseId;
        }
        
        const response = await fetch(`${API_V2_BASE}/search/disease`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!data.success) {
            throw new Error(data.message || 'Search failed');
        }
        
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to search drugs. Please try again.');
    } finally {
        setLoadingState(diseaseSearchBtn, false);
    }
}

/**
 * Display search results
 */
function displayResults(data) {
    // Query type
    const queryTypeMap = {
        'symptom': 'Symptom-Based Search',
        'disease': 'Disease-Based Search',
        'drug_similarity': 'Drug Similarity Search'
    };
    document.getElementById('queryType').textContent = queryTypeMap[data.query_type] || data.query_type;
    
    // Query input
    const queryInput = document.getElementById('queryInput');
    if (data.query_type === 'symptom') {
        queryInput.textContent = data.query_input.symptoms.join(', ');
    } else if (data.query_type === 'disease') {
        queryInput.textContent = data.query_input.disease_name;
    }
    
    // Results count
    document.getElementById('resultsCount').textContent = data.total_found;
    
    // Execution time
    const executionTime = data.search_metadata?.execution_time_ms || 0;
    document.getElementById('executionTime').textContent = `${executionTime}ms`;
    
    // Drug recommendations
    const drugsContainer = document.getElementById('drugsList');
    drugsContainer.innerHTML = '';
    
    if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach((drug, index) => {
            const card = createDrugCard(drug, index + 1);
            drugsContainer.appendChild(card);
        });
    } else {
        drugsContainer.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                <p style="font-size: 1.25rem; margin-bottom: 0.5rem;">No drugs found</p>
                <p>Try adjusting your search criteria or lowering the similarity threshold.</p>
            </div>
        `;
    }
    
    showResults();
}

/**
 * Create drug card element
 */
function createDrugCard(drug, rank) {
    const card = document.createElement('div');
    card.className = 'drug-card';
    
    // Determine score color
    const score = drug.similarity_score;
    let scoreClass = 'score-medium';
    if (score >= 0.9) scoreClass = 'score-high';
    else if (score < 0.75) scoreClass = 'score-low';
    
    card.innerHTML = `
        <div class="drug-header">
            <div class="drug-info">
                <div class="drug-name">${rank}. ${drug.drug_name}</div>
                <div class="drug-id">${drug.drug_id}</div>
            </div>
            <div class="score-badge ${scoreClass}">
                <div class="score-value">${(score * 100).toFixed(0)}%</div>
                <div class="score-label">Similarity</div>
            </div>
        </div>
        
        <div class="drug-explanation">
            <div class="explanation-label">Why this drug?</div>
            <div class="explanation-text">${drug.explanation}</div>
        </div>
        
        ${drug.treats_conditions && drug.treats_conditions.length > 0 ? `
            <div class="conditions-section">
                <div class="conditions-label">Treats:</div>
                <div class="conditions-tags">
                    ${drug.treats_conditions.map(condition => 
                        `<span class="condition-tag">${condition}</span>`
                    ).join('')}
                </div>
            </div>
        ` : ''}
    `;
    
    return card;
}

/**
 * Set button loading state
 */
function setLoadingState(button, isLoading) {
    const btnText = button.querySelector('.btn-text');
    const btnLoading = button.querySelector('.btn-loading');
    
    if (isLoading) {
        button.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
    } else {
        button.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
}

/**
 * Show results section
 */
function showResults() {
    resultsSection.style.display = 'block';
    
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
    console.log('Medical Assistant v2.0 initialized');
    console.log('API Base:', API_V2_BASE);
    
    // Focus on first symptom input
    const firstInput = document.querySelector('.symptom-field');
    if (firstInput) {
        firstInput.focus();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
