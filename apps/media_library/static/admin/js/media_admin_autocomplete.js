/**
 * Media Admin Autocomplete for Content Object Selection
 * Provides a professional search interface for selecting content objects
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAutocomplete);
    } else {
        initAutocomplete();
    }

    function initAutocomplete() {
        const contentTypeField = document.getElementById('id_content_type');
        const searchField = document.getElementById('id_content_object_search');
        const objectIdField = document.getElementById('id_object_id');

        if (!contentTypeField || !searchField || !objectIdField) {
            return; // Fields not found, exit
        }

        // Create autocomplete dropdown
        const dropdown = document.createElement('div');
        dropdown.id = 'content-object-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            background: var(--body-bg, white);
            border: 1px solid var(--border-color, #ccc);
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
            display: none;
            z-index: 9999;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-width: 300px;
        `;
        searchField.parentNode.appendChild(dropdown);

        // Position dropdown below search field
        function positionDropdown() {
            const rect = searchField.getBoundingClientRect();
            dropdown.style.top = (rect.bottom + window.scrollY) + 'px';
            dropdown.style.left = rect.left + 'px';
            dropdown.style.width = rect.width + 'px';
        }

        // Enable/disable search field based on content type selection
        contentTypeField.addEventListener('change', function() {
            if (this.value) {
                searchField.disabled = false;
                searchField.placeholder = 'Start typing to search...';
                searchField.value = '';
                objectIdField.value = '';
            } else {
                searchField.disabled = true;
                searchField.placeholder = 'First select a content type above';
                searchField.value = '';
                objectIdField.value = '';
                dropdown.style.display = 'none';
            }
        });

        // Initialize state
        if (!contentTypeField.value) {
            searchField.disabled = true;
        }

        // Debounce function
        let searchTimeout;
        function debounce(func, wait) {
            return function executedFunction(...args) {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => func(...args), wait);
            };
        }

        // Search function
        async function searchContentObjects(query) {
            const contentTypeId = contentTypeField.value;
            
            if (!contentTypeId || query.length < 1) {
                dropdown.style.display = 'none';
                return;
            }

            try {
                const url = `/admin/media_library/media/search-content-objects/?content_type_id=${contentTypeId}&q=${encodeURIComponent(query)}`;
                const response = await fetch(url);
                const data = await response.json();

                if (data.results && data.results.length > 0) {
                    displayResults(data.results);
                } else {
                    displayNoResults();
                }
            } catch (error) {
                console.error('Search error:', error);
                displayError();
            }
        }

        // Display results
        function displayResults(results) {
            dropdown.innerHTML = '';
            
            results.forEach(result => {
                const item = document.createElement('div');
                item.style.cssText = `
                    padding: 10px 15px;
                    cursor: pointer;
                    border-bottom: 1px solid var(--border-color, #eee);
                    color: var(--body-fg, #333);
                    transition: background-color 0.2s;
                `;
                item.textContent = result.text;
                
                item.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = 'var(--selected-bg, #e3f2fd)';
                });
                
                item.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = 'transparent';
                });
                
                item.addEventListener('click', function() {
                    selectObject(result);
                });
                
                dropdown.appendChild(item);
            });

            positionDropdown();
            dropdown.style.display = 'block';
        }

        // Display no results message
        function displayNoResults() {
            dropdown.innerHTML = `
                <div style="padding: 15px; text-align: center; color: var(--body-fg, #666); font-style: italic;">
                    No results found
                </div>
            `;
            positionDropdown();
            dropdown.style.display = 'block';
        }

        // Display error message
        function displayError() {
            dropdown.innerHTML = `
                <div style="padding: 15px; text-align: center; color: #d32f2f;">
                    Error loading results
                </div>
            `;
            positionDropdown();
            dropdown.style.display = 'block';
        }

        // Select an object
        function selectObject(result) {
            searchField.value = result.text;
            objectIdField.value = result.id;
            dropdown.style.display = 'none';
            
            // Show success feedback
            searchField.style.borderColor = '#4caf50';
            setTimeout(() => {
                searchField.style.borderColor = '';
            }, 2000);
        }

        // Event listeners
        searchField.addEventListener('input', debounce(function(e) {
            searchContentObjects(e.target.value);
        }, 300));

        searchField.addEventListener('focus', function() {
            if (this.value && contentTypeField.value) {
                searchContentObjects(this.value);
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (e.target !== searchField && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // Handle keyboard navigation
        let selectedIndex = -1;
        searchField.addEventListener('keydown', function(e) {
            const items = dropdown.querySelectorAll('div[style*="cursor: pointer"]');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                highlightItem(items, selectedIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, 0);
                highlightItem(items, selectedIndex);
            } else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                items[selectedIndex].click();
            } else if (e.key === 'Escape') {
                dropdown.style.display = 'none';
                selectedIndex = -1;
            }
        });

        function highlightItem(items, index) {
            items.forEach((item, i) => {
                if (i === index) {
                    item.style.backgroundColor = 'var(--selected-bg, #e3f2fd)';
                    item.scrollIntoView({ block: 'nearest' });
                } else {
                    item.style.backgroundColor = 'transparent';
                }
            });
        }
    }
})();
