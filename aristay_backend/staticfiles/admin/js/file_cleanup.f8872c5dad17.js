/**
 * File Cleanup Management JavaScript
 * Handles API calls for file cleanup operations with CSRF protection
 */

// Global variables
let isLoading = false;

// Utility Functions
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                  document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    return token;
}

function showLoading() {
    isLoading = true;
    document.getElementById('loading').classList.add('show');
    
    // Disable all action buttons
    document.querySelectorAll('.action-card button').forEach(btn => {
        btn.disabled = true;
    });
}

function hideLoading() {
    isLoading = false;
    document.getElementById('loading').classList.remove('show');
    
    // Re-enable all action buttons
    document.querySelectorAll('.action-card button').forEach(btn => {
        btn.disabled = false;
    });
}

function showResults(title, content) {
    document.getElementById('results-title').textContent = title;
    document.getElementById('results-content').innerHTML = content;
    document.getElementById('results-container').classList.add('show');
    
    // Scroll to results
    document.getElementById('results-container').scrollIntoView({ behavior: 'smooth' });
}

function hideResults() {
    document.getElementById('results-container').classList.remove('show');
}

function showAlert(message, type = 'info') {
    return `<div class="alert alert-${type}">${message}</div>`;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
}

// API Functions
async function makeApiCall(action, data = {}) {
    if (isLoading) {
        console.warn('API call blocked - already loading');
        return null;
    }

    showLoading();

    try {
        const requestData = {
            action: action,
            ...data
        };

        const response = await fetch('/api/file-cleanup/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'API request failed');
        }

        return result;

    } catch (error) {
        console.error('API call error:', error);
        showResults('Error', showAlert(`Error: ${error.message}`, 'danger'));
        return null;
    } finally {
        hideLoading();
    }
}

// Main Action Functions
async function getStorageStats() {
    const result = await makeApiCall('stats');
    if (!result) return;

    const stats = result.stats;
    
    const statsHtml = `
        ${showAlert('Storage statistics retrieved successfully', 'success')}
        
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">${stats.total_files}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${stats.total_size_mb} MB</div>
                <div class="stat-label">Total Size</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${stats.total_size_gb} GB</div>
                <div class="stat-label">Size (GB)</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${stats.age_span_days}</div>
                <div class="stat-label">Age Span (Days)</div>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div>
                <strong>📅 Oldest File:</strong> ${formatDate(stats.oldest_file)}
            </div>
            <div>
                <strong>📅 Newest File:</strong> ${formatDate(stats.newest_file)}
            </div>
        </div>
        
        ${stats.total_files === 0 ? 
            showAlert('No import files found in storage.', 'info') : 
            `<div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                💡 <strong>Tip:</strong> Regular cleanup helps maintain optimal system performance. 
                Consider keeping 30-90 days of files based on your business needs.
            </div>`
        }
    `;

    showResults('📊 Storage Statistics', statsHtml);
}

async function getSuggestions() {
    const targetSize = parseInt(document.getElementById('target-size').value) || 100;
    
    if (targetSize < 1 || targetSize > 10000) {
        showResults('Error', showAlert('Please enter a target size between 1 and 10,000 MB', 'warning'));
        return;
    }

    const result = await makeApiCall('suggest', { target_mb: targetSize });
    if (!result) return;

    const suggestion = result.suggestion;
    
    let suggestionHtml = `
        ${showAlert('Cleanup suggestion generated', 'success')}
        
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">${suggestion.current_size_mb} MB</div>
                <div class="stat-label">Current Size</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${suggestion.target_size_mb} MB</div>
                <div class="stat-label">Target Size</div>
            </div>
        </div>
    `;

    if (!suggestion.action_needed) {
        suggestionHtml += showAlert('✅ Great! Your storage is already within the target limits. No cleanup needed.', 'success');
    } else {
        if (suggestion.recommended_days_to_keep) {
            suggestionHtml += `
                ${showAlert(`📋 Recommendation: ${suggestion.message}`, 'info')}
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 4px; margin: 15px 0;">
                    <h4 style="margin: 0 0 10px 0; color: #856404;">💡 Recommended Action:</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #856404;">
                        <li>Keep files from the last <strong>${suggestion.recommended_days_to_keep} days</strong></li>
                        <li>This would delete <strong>${suggestion.files_to_delete} files</strong></li>
                        <li>Free up <strong>${suggestion.space_to_free_mb} MB</strong> of space</li>
                        <li>Final storage size: <strong>${suggestion.projected_final_size_mb} MB</strong></li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button type="button" class="btn btn-info" onclick="previewCleanupWithDays(${suggestion.recommended_days_to_keep})">
                        🔍 Preview This Cleanup
                    </button>
                    <button type="button" class="btn btn-danger" onclick="confirmCleanupWithDays(${suggestion.recommended_days_to_keep})" style="margin-left: 10px;">
                        🗑️ Perform This Cleanup
                    </button>
                </div>
            `;
        } else {
            suggestionHtml += `
                ${showAlert(`⚠️ ${suggestion.message}`, 'warning')}
                <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                    <strong>💡 ${suggestion.recommendation}</strong>
                </div>
            `;
        }
    }

    showResults('💡 Cleanup Suggestions', suggestionHtml);
}

async function runDryRun() {
    const days = parseInt(document.getElementById('dry-run-days').value) || 30;
    
    if (days < 1 || days > 365) {
        showResults('Error', showAlert('Please enter a number of days between 1 and 365', 'warning'));
        return;
    }

    const result = await makeApiCall('dry_run', { days: days });
    if (!result) return;

    const dryRunResult = result.result;
    
    let resultHtml = `
        ${showAlert(`Dry run completed - showing what would be deleted (keeping last ${days} days)`, 'info')}
        
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">${dryRunResult.files_found}</div>
                <div class="stat-label">Files Found</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${dryRunResult.total_size_mb} MB</div>
                <div class="stat-label">Would Free</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${formatDate(dryRunResult.cutoff_date)}</div>
                <div class="stat-label">Cutoff Date</div>
            </div>
        </div>
    `;

    if (dryRunResult.files_found === 0) {
        resultHtml += showAlert('✅ No files found that are older than the specified retention period.', 'success');
    } else {
        resultHtml += `
            <div style="margin: 20px 0;">
                ${showAlert(`Found ${dryRunResult.files_found} files that would be deleted, freeing ${dryRunResult.total_size_mb} MB of space.`, 'warning')}
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button type="button" class="btn btn-danger" onclick="confirmCleanupWithDays(${days})">
                    🗑️ Perform Cleanup (Delete ${dryRunResult.files_found} Files)
                </button>
            </div>
        `;

        // Show file details if available and not too many
        if (dryRunResult.files && dryRunResult.files.length > 0 && dryRunResult.files.length <= 50) {
            resultHtml += `
                <h4 style="margin: 20px 0 10px 0;">Files to be deleted:</h4>
                <table class="file-table">
                    <thead>
                        <tr>
                            <th>File Name</th>
                            <th>Size</th>
                            <th>Import Date</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            dryRunResult.files.slice(0, 20).forEach(file => {
                resultHtml += `
                    <tr>
                        <td>${file.file_name || 'N/A'}</td>
                        <td>${formatBytes(file.size)}</td>
                        <td>${formatDate(file.imported_at)}</td>
                    </tr>
                `;
            });
            
            resultHtml += '</tbody></table>';
            
            if (dryRunResult.files.length > 20) {
                resultHtml += `<p style="margin-top: 10px; color: #666; font-style: italic;">... and ${dryRunResult.files.length - 20} more files</p>`;
            }
        }
    }

    showResults('🔍 Dry Run Results', resultHtml);
}

function confirmCleanup() {
    const days = parseInt(document.getElementById('cleanup-days').value) || 30;
    confirmCleanupWithDays(days);
}

function confirmCleanupWithDays(days) {
    if (days < 1 || days > 365) {
        showResults('Error', showAlert('Please enter a number of days between 1 and 365', 'warning'));
        return;
    }

    document.getElementById('dialog-message').innerHTML = `
        <p><strong>⚠️ This will permanently delete import files older than ${days} days.</strong></p>
        <p>This action cannot be undone. Are you sure you want to proceed?</p>
        <p style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 4px; color: #856404;">
            💡 <strong>Tip:</strong> Consider running a dry run first to see exactly what will be deleted.
        </p>
    `;
    
    // Store days in the dialog for later use
    document.getElementById('confirmation-dialog').setAttribute('data-days', days);
    document.getElementById('confirmation-dialog').classList.add('show');
}

function showConfirmation() {
    document.getElementById('confirmation-dialog').classList.add('show');
}

function hideConfirmation() {
    document.getElementById('confirmation-dialog').classList.remove('show');
}

async function performCleanup() {
    hideConfirmation();
    
    const days = parseInt(document.getElementById('confirmation-dialog').getAttribute('data-days')) || 30;
    
    const result = await makeApiCall('cleanup', { days: days });
    if (!result) return;

    const cleanupResult = result.result;
    
    let resultHtml = `
        ${showAlert(`Cleanup completed successfully! (kept files from last ${days} days)`, 'success')}
        
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">${cleanupResult.files_deleted}</div>
                <div class="stat-label">Files Deleted</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${cleanupResult.space_freed_mb} MB</div>
                <div class="stat-label">Space Freed</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${formatDate(cleanupResult.cutoff_date)}</div>
                <div class="stat-label">Cutoff Date</div>
            </div>
        </div>
    `;

    if (cleanupResult.files_deleted === 0) {
        resultHtml += showAlert('ℹ️ No files were found that needed to be deleted.', 'info');
    } else {
        resultHtml += `
            <div style="background: #d4edda; padding: 15px; border-radius: 4px; margin: 15px 0; color: #155724;">
                <h4 style="margin: 0 0 10px 0;">✅ Cleanup Summary:</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Successfully deleted <strong>${cleanupResult.files_deleted}</strong> old import files</li>
                    <li>Freed up <strong>${cleanupResult.space_freed_mb} MB</strong> of storage space</li>
                    <li>System performance should be improved</li>
                </ul>
            </div>
        `;
    }

    // Show errors if any occurred
    if (cleanupResult.errors && cleanupResult.errors.length > 0) {
        resultHtml += `
            <div style="margin-top: 20px;">
                ${showAlert('Some errors occurred during cleanup:', 'warning')}
                <ul style="margin: 10px 0; padding-left: 20px;">
        `;
        
        cleanupResult.errors.forEach(error => {
            resultHtml += `<li>${error}</li>`;
        });
        
        resultHtml += '</ul></div>';
    }

    resultHtml += `
        <div style="text-align: center; margin-top: 20px;">
            <button type="button" class="btn btn-primary" onclick="getStorageStats()">
                📊 View Updated Storage Stats
            </button>
        </div>
    `;

    showResults('🗑️ Cleanup Results', resultHtml);
}

function previewCleanupWithDays(days) {
    document.getElementById('dry-run-days').value = days;
    runDryRun();
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Close confirmation dialog when clicking outside
    document.getElementById('confirmation-dialog').addEventListener('click', function(e) {
        if (e.target === this) {
            hideConfirmation();
        }
    });
    
    // Handle escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (document.getElementById('confirmation-dialog').classList.contains('show')) {
                hideConfirmation();
            } else if (document.getElementById('results-container').classList.contains('show')) {
                hideResults();
            }
        }
    });
    
    console.log('File cleanup management interface loaded');
});