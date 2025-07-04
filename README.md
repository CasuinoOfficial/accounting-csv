# Investment Portfolio Analysis Tool

## Overview

This tool provides comprehensive analysis of your investment portfolio's profit and loss (PNL) data from chunked CSV files. It helps investment professionals understand performance, identify trends, and make data-driven decisions with full blockchain verification capabilities. The tool automatically detects and processes multiple chunk files, combining them into unified analysis reports.

## 🎯 Key Features

- **Financial Analysis**: Total PNL, win rates, profit/loss ratios, risk metrics
- **Time-Based Insights**: Daily/hourly/monthly performance patterns
- **Transaction Breakdown**: Revenue analysis by source and type
- **Risk Assessment**: Volatility measurements and percentile analysis
- **Blockchain Verification**: Verify all transactions on Sui network explorers
- **Professional Reports**: Detailed analysis with JSON export capability

## ⚡ Quick Start

1. **Install Python**: Download from [python.org](https://www.python.org/downloads/)
2. **Download Files**: Get all analysis files and put your CSV chunk files in the same folder
3. **Open Terminal/Command Prompt**: 
   - **Mac**: `Cmd + Space` → type "Terminal" → Enter
   - **Windows**: `Win + R` → type "cmd" → Enter, or Shift+right-click in folder → "Open command window here"
4. **Navigate to Folder**: Type `cd ` then drag your folder into the terminal window
5. **Run Analysis**: Type `python3 GetTotalPNL.py --auto-chunks` and press Enter

## 💻 Command Line Instructions

### Navigate to Your Files
**Mac/Linux**: Type `cd ` then drag the folder from Finder into Terminal  
**Windows**: Type `cd ` then paste the folder path from File Explorer address bar

### Verify Location
**Mac/Linux**: Type `ls` to see your files  
**Windows**: Type `dir` to see your files

### File Names with Spaces
Always use quotes: `python3 GetTotalPNL.py "My Portfolio Data.csv"`

## 📊 Usage Examples

```bash
# Auto-detect and analyze chunk files (RECOMMENDED - primary usage)
python3 GetTotalPNL.py --auto-chunks

# Combine chunk processing with JSON export
python3 GetTotalPNL.py --auto-chunks --export-json

# Analyze multiple specific chunk files manually
python3 GetTotalPNL.py chunk_1.csv chunk_2.csv chunk_3.csv chunk_4.csv

# Analyze single file
python3 GetTotalPNL.py your_data.csv

# Export detailed analysis to JSON
python3 GetTotalPNL.py --auto-chunks --export-json

# Show help
python3 GetTotalPNL.py --help
```

## 📁 CSV File Requirements

Your chunk files (chunk_1.csv, chunk_2.csv, etc.) must contain these columns:
- **Digest**: Blockchain transaction hash
- **Timestamp**: Date/time (YYYY-MM-DD HH:MM:SS format)
- **Type**: Transaction category (e.g., "Fee Revenue", "Staking Revenue")
- **PNL USD**: Profit/Loss amount (positive or negative numbers)

The tool automatically detects files named `chunk_1.csv`, `chunk_2.csv`, `chunk_3.csv`, etc. in your directory.

## 🔍 Blockchain Verification

Each transaction digest can be verified on Sui network explorers:
- **[Suivision](https://suivision.xyz/)**: Paste digest in search bar
- **[Suiscan](https://suiscan.xyz/)**: Enter digest to view transaction details

**Verification Steps**: Copy digest → Visit explorer → Paste → Confirm amount/timestamp match

## 📋 Report Sections Explained

### Overall Statistics
- **Total PNL**: Net profit/loss across all transactions
- **Win Rate**: Percentage of profitable transactions
- **Volatility**: Risk measurement via standard deviation
- **Percentiles**: Performance distribution analysis

### Time Analysis
- **Best/Worst Days**: Highest/lowest performing dates
- **Profitable Days**: Percentage of days with positive returns
- **Optimal Hours**: Best performing times for activity

### Transaction Types
- **Revenue Sources**: Income breakdown by category
- **Contribution %**: Each source's share of total PNL
- **Performance**: Average PNL per transaction type

## 🛠 Advanced Features

- **Multi-File Processing**: Analyze multiple CSV files simultaneously
- **Automatic Chunk Detection**: Automatically finds and processes chunk_1.csv, chunk_2.csv, etc.
- **JSON Export**: Machine-readable data for Excel/PowerBI integration
- **Progress Tracking**: Real-time processing updates for large files
- **Data Quality**: Automatic validation and error reporting
- **Statistical Analysis**: Comprehensive risk and performance metrics

### Chunk File Processing

If you've split your large CSV into multiple chunks, the tool can handle them automatically:

**Auto-Detection**: Use `--auto-chunks` to automatically find files named:
- `chunk_1.csv`, `chunk_2.csv`, `chunk_3.csv`, etc.
- `chunk1.csv`, `chunk2.csv`, `chunk3.csv`, etc.
- `part_1.csv`, `part_2.csv`, etc.

**Manual Selection**: Specify multiple files directly:
```bash
python3 GetTotalPNL.py chunk_1.csv chunk_2.csv chunk_3.csv chunk_4.csv
```

The tool will combine all chunks and provide unified analysis across all files, plus a breakdown showing contribution from each chunk.

## 🔧 Troubleshooting

**Python Issues**
- "Command not found": Install Python from [python.org](https://www.python.org/downloads/)
- Windows: Check "Add Python to PATH" during installation
- Try `python` instead of `python3`

**File Issues**
- "No chunk files found": Ensure your chunk files are named chunk_1.csv, chunk_2.csv, etc.
- "File not found": Ensure chunk files are in same folder as script
- "Permission denied": Close Excel/other programs using the chunk files
- Use quotes around filenames with spaces

**Navigation Issues**
- Can't find folder: Use drag-and-drop method described above
- Wrong directory: Use `ls` (Mac/Linux) or `dir` (Windows) to check location
- No chunks detected: Verify your files follow the naming pattern (chunk_1.csv, chunk_2.csv, etc.)

## 🔒 Security & Privacy

- All analysis performed locally on your computer
- No data sent to external servers
- Blockchain verification uses public explorers only
- Complete transaction privacy maintained

## 📈 Business Value

**Optimize Performance**: Identify best-performing periods and transaction types  
**Manage Risk**: Understand volatility patterns and worst-case scenarios  
**Generate Reports**: Create professional analysis for stakeholders  
**Ensure Transparency**: Verify all transactions with blockchain records  
**Make Data-Driven Decisions**: Use statistical insights to improve returns

## 📞 Support

For technical issues, contact your IT department. 

**Processing Time**: Typical chunk processing (4 files, 3.3M+ records) takes 2-3 minutes. Press Ctrl+C to interrupt if needed.

**Most Common Usage**: `python3 GetTotalPNL.py --auto-chunks`

---

*Professional investment analysis tool with blockchain verification capabilities*