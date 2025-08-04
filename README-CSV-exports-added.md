## New CSV Export Features
- Export Button:

Added a green "Export CSV" button next to the "Add Equipment" button on the main dashboard
Uses a download icon for clear visual indication

### Export Functionality:

- Route: /export/csv - handles the CSV generation and download
- Filename: Automatically timestamped (e.g., equipment_export_20250803_143022.csv)
- Complete Data: Exports all equipment fields plus calculated profit/loss

### CSV Columns Included:

- ID
- Description
- Purchase Cost
- Purchase Date
- Current Retail
- Current Resale
- Resale Location
- Condition
- Date Added
- Last Updated
- Profit/Loss (calculated automatically)

### How It Works

Click the "Export CSV" button on the main dashboard
Your browser will automatically download a CSV file with all your equipment data
The file includes a timestamp in the filename to avoid conflicts
You can open it in Excel, Google Sheets, or any spreadsheet application

### Key Benefits

- Data Backup: Easy way to backup your equipment data
- Analysis: Import into spreadsheet applications for advanced analysis
- Sharing: Send equipment lists to others
- Records: Keep historical snapshots of your inventory

The CSV export respects all your current data and includes calculated fields like profit/loss for each item. The export works whether you have 1 item or 1000 items in your inventory!