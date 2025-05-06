
# Chrome Extension Backup code

```
// Create a function to get all extensions and export to CSV
function exportExtensionsToCSV() {
  chrome.management.getAll(function(extensions) {
    // Filter out Chrome apps and only keep extensions
    const filteredExtensions = extensions.filter(ext => ext.type === 'extension');
    
    // Prepare CSV content
    let csvContent = "Name,ID,Enabled,Link\n";
    
    filteredExtensions.forEach(ext => {
      const link = `https://chrome.google.com/webstore/detail/${ext.id}`;
      csvContent += `"${ext.name}","${ext.id}",${ext.enabled},"${link}"\n`;
    });
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'chrome_extensions_backup.csv');
    link.style.visibility = 'hidden';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });
}

// Run the function
exportExtensionsToCSV();
```
