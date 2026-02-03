// Resume PDF Export Functionality
// This script helps export the resume to PDF

function exportToPDF() {
    // Use browser's print to PDF functionality
    window.print();
}

// Add keyboard shortcut (Ctrl/Cmd + P)
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        exportToPDF();
    }
});

// Optional: Add a print button (uncomment if needed)
/*
function addPrintButton() {
    const button = document.createElement('button');
    button.textContent = 'Export to PDF';
    button.style.cssText = 'position: fixed; top: 20px; right: 20px; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; z-index: 1000;';
    button.onclick = exportToPDF;
    document.body.appendChild(button);
}

// Uncomment to add print button
// addPrintButton();
*/

