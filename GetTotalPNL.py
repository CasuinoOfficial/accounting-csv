#!/usr/bin/env python3
"""
Advanced PNL Analysis Tool
Provides comprehensive analysis of trading/revenue data from CSV files
Supports multiple files and automatic chunk processing
"""

import csv
import argparse
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict, OrderedDict
import statistics
import json
from pathlib import Path
import re
import glob

class PNLAnalyzer:
    def __init__(self, csv_files):
        self.csv_files = csv_files if isinstance(csv_files, list) else [csv_files]
        self.data = []
        self.total_pnl = Decimal('0')
        self.record_count = 0
        self.valid_pnl_count = 0
        self.invalid_records = []
        self.pnl_values = []
        self.daily_pnl = defaultdict(Decimal)
        self.type_pnl = defaultdict(Decimal)
        self.type_counts = defaultdict(int)
        self.hourly_pnl = defaultdict(Decimal)
        self.monthly_pnl = defaultdict(Decimal)
        self.file_stats = {}  # Track stats per file
        
    def load_data(self):
        """Load and parse CSV data from multiple files with progress tracking"""
        print(f"Loading data from {len(self.csv_files)} file(s)...")
        print("This may take a moment for large files...")
        
        total_files = len(self.csv_files)
        
        for file_idx, csv_file in enumerate(self.csv_files, 1):
            print(f"\nProcessing file {file_idx}/{total_files}: {csv_file}")
            
            if not self._load_single_file(csv_file):
                print(f"Failed to load {csv_file}")
                continue
        
        if self.valid_pnl_count == 0:
            print("No valid data found in any files!")
            return False
        
        print(f"\nData loading complete! Processed {self.record_count:,} total records across {len(self.csv_files)} files.")
        return True
    
    def _load_single_file(self, csv_file):
        """Load data from a single CSV file"""
        file_record_count = 0
        file_valid_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                # Validate required columns
                required_columns = ['PNL USD', 'Timestamp', 'Type']
                missing_columns = [col for col in required_columns if col not in csv_reader.fieldnames]
                if missing_columns:
                    print(f"Error: Missing required columns in {csv_file}: {missing_columns}")
                    print(f"Available columns: {csv_reader.fieldnames}")
                    return False
                
                # Process each row with progress tracking
                for i, row in enumerate(csv_reader):
                    if i % 100000 == 0 and i > 0:
                        print(f"  Processed {i:,} records in {csv_file}...")
                    
                    self.record_count += 1
                    file_record_count += 1
                    
                    try:
                        # Parse PNL value
                        pnl_str = row['PNL USD'].strip()
                        if not pnl_str:
                            continue
                            
                        pnl_value = Decimal(pnl_str)
                        
                        # Parse timestamp
                        timestamp_str = row['Timestamp'].strip()
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        # Parse transaction type
                        tx_type = row['Type'].strip()
                        
                        # Store data
                        record = {
                            'pnl': pnl_value,
                            'timestamp': timestamp,
                            'type': tx_type,
                            'digest': row.get('Digest', '').strip(),
                            'source_file': csv_file
                        }
                        
                        self.data.append(record)
                        self.total_pnl += pnl_value
                        self.pnl_values.append(float(pnl_value))
                        self.valid_pnl_count += 1
                        file_valid_count += 1
                        
                        # Aggregate by different time periods
                        date_key = timestamp.date()
                        self.daily_pnl[date_key] += pnl_value
                        
                        hour_key = timestamp.hour
                        self.hourly_pnl[hour_key] += pnl_value
                        
                        month_key = timestamp.strftime('%Y-%m')
                        self.monthly_pnl[month_key] += pnl_value
                        
                        # Aggregate by transaction type
                        self.type_pnl[tx_type] += pnl_value
                        self.type_counts[tx_type] += 1
                        
                    except (InvalidOperation, ValueError, KeyError) as e:
                        self.invalid_records.append({
                            'row_number': self.record_count,
                            'error': str(e),
                            'raw_data': row,
                            'source_file': csv_file
                        })
                        continue
                
                # Store file statistics
                self.file_stats[csv_file] = {
                    'total_records': file_record_count,
                    'valid_records': file_valid_count,
                    'invalid_records': file_record_count - file_valid_count
                }
                
                print(f"  Completed {csv_file}: {file_record_count:,} records, {file_valid_count:,} valid")
                return True
                
        except FileNotFoundError:
            print(f"Error: File '{csv_file}' not found")
            return False
        except Exception as e:
            print(f"Error reading CSV file {csv_file}: {e}")
            return False
    
    def calculate_statistics(self):
        """Calculate comprehensive statistics"""
        if not self.pnl_values:
            return {}
        
        pnl_sorted = sorted(self.pnl_values)
        
        return {
            'total': float(self.total_pnl),
            'count': self.valid_pnl_count,
            'mean': statistics.mean(self.pnl_values),
            'median': statistics.median(self.pnl_values),
            'mode': statistics.mode(self.pnl_values) if len(set(self.pnl_values)) < len(self.pnl_values) else None,
            'std_dev': statistics.stdev(self.pnl_values) if len(self.pnl_values) > 1 else 0,
            'variance': statistics.variance(self.pnl_values) if len(self.pnl_values) > 1 else 0,
            'min': min(self.pnl_values),
            'max': max(self.pnl_values),
            'range': max(self.pnl_values) - min(self.pnl_values),
            'percentile_25': pnl_sorted[len(pnl_sorted) // 4],
            'percentile_75': pnl_sorted[3 * len(pnl_sorted) // 4],
            'percentile_90': pnl_sorted[9 * len(pnl_sorted) // 10],
            'percentile_95': pnl_sorted[95 * len(pnl_sorted) // 100],
            'percentile_99': pnl_sorted[99 * len(pnl_sorted) // 100],
        }
    
    def analyze_profit_loss(self):
        """Analyze profit vs loss breakdown"""
        profits = [x for x in self.pnl_values if x > 0]
        losses = [x for x in self.pnl_values if x < 0]
        breakeven = [x for x in self.pnl_values if x == 0]
        
        return {
            'profit_transactions': len(profits),
            'loss_transactions': len(losses),
            'breakeven_transactions': len(breakeven),
            'total_profit': sum(profits),
            'total_loss': sum(losses),
            'win_rate': len(profits) / len(self.pnl_values) * 100 if self.pnl_values else 0,
            'avg_profit': statistics.mean(profits) if profits else 0,
            'avg_loss': statistics.mean(losses) if losses else 0,
            'largest_profit': max(profits) if profits else 0,
            'largest_loss': min(losses) if losses else 0,
            'profit_loss_ratio': abs(statistics.mean(profits) / statistics.mean(losses)) if profits and losses else 0
        }
    
    def analyze_time_performance(self):
        """Analyze performance by time periods"""
        # Daily analysis
        daily_stats = {}
        if self.daily_pnl:
            daily_values = [float(v) for v in self.daily_pnl.values()]
            daily_stats = {
                'best_day': max(self.daily_pnl.items(), key=lambda x: x[1]),
                'worst_day': min(self.daily_pnl.items(), key=lambda x: x[1]),
                'avg_daily_pnl': statistics.mean(daily_values),
                'daily_volatility': statistics.stdev(daily_values) if len(daily_values) > 1 else 0,
                'profitable_days': len([v for v in daily_values if v > 0]),
                'total_days': len(daily_values)
            }
        
        # Hourly analysis
        hourly_stats = {}
        if self.hourly_pnl:
            hourly_stats = {
                'best_hour': max(self.hourly_pnl.items(), key=lambda x: x[1]),
                'worst_hour': min(self.hourly_pnl.items(), key=lambda x: x[1]),
                'hourly_breakdown': dict(self.hourly_pnl)
            }
        
        # Monthly analysis
        monthly_stats = {}
        if self.monthly_pnl:
            monthly_values = [float(v) for v in self.monthly_pnl.values()]
            monthly_stats = {
                'best_month': max(self.monthly_pnl.items(), key=lambda x: x[1]),
                'worst_month': min(self.monthly_pnl.items(), key=lambda x: x[1]),
                'avg_monthly_pnl': statistics.mean(monthly_values),
                'monthly_breakdown': dict(self.monthly_pnl)
            }
        
        return {
            'daily': daily_stats,
            'hourly': hourly_stats,
            'monthly': monthly_stats
        }
    
    def analyze_transaction_types(self):
        """Analyze performance by transaction type"""
        type_analysis = {}
        
        for tx_type, total_pnl in self.type_pnl.items():
            count = self.type_counts[tx_type]
            type_records = [r for r in self.data if r['type'] == tx_type]
            type_pnl_values = [float(r['pnl']) for r in type_records]
            
            type_analysis[tx_type] = {
                'total_pnl': float(total_pnl),
                'count': count,
                'avg_pnl': float(total_pnl) / count if count > 0 else 0,
                'min_pnl': min(type_pnl_values) if type_pnl_values else 0,
                'max_pnl': max(type_pnl_values) if type_pnl_values else 0,
                'std_dev': statistics.stdev(type_pnl_values) if len(type_pnl_values) > 1 else 0,
                'contribution_percent': float(total_pnl) / float(self.total_pnl) * 100 if self.total_pnl != 0 else 0
            }
        
        return type_analysis
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("=" * 80)
        print("COMPREHENSIVE PNL ANALYSIS REPORT")
        print("=" * 80)
        
        # Basic information
        print(f"\nFILES ANALYZED: {len(self.csv_files)}")
        for i, csv_file in enumerate(self.csv_files, 1):
            stats = self.file_stats.get(csv_file, {})
            print(f"  {i}. {csv_file}")
            print(f"     Records: {stats.get('total_records', 0):,}, Valid: {stats.get('valid_records', 0):,}")
        
        print(f"\nANALYSIS DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"TOTAL RECORDS: {self.record_count:,}")
        print(f"VALID PNL RECORDS: {self.valid_pnl_count:,}")
        print(f"INVALID RECORDS: {len(self.invalid_records):,}")
        
        if self.data:
            date_range = f"{min(r['timestamp'] for r in self.data).date()} to {max(r['timestamp'] for r in self.data).date()}"
            print(f"DATE RANGE: {date_range}")
        
        # Overall statistics
        stats = self.calculate_statistics()
        print(f"\n{'='*50}")
        print("OVERALL STATISTICS")
        print(f"{'='*50}")
        print(f"Total PNL:           ${stats['total']:,.2f}")
        print(f"Average PNL:         ${stats['mean']:,.6f}")
        print(f"Median PNL:          ${stats['median']:,.6f}")
        print(f"Standard Deviation:  ${stats['std_dev']:,.6f}")
        print(f"Minimum PNL:         ${stats['min']:,.6f}")
        print(f"Maximum PNL:         ${stats['max']:,.6f}")
        print(f"Range:               ${stats['range']:,.6f}")
        print(f"25th Percentile:     ${stats['percentile_25']:,.6f}")
        print(f"75th Percentile:     ${stats['percentile_75']:,.6f}")
        print(f"90th Percentile:     ${stats['percentile_90']:,.6f}")
        print(f"95th Percentile:     ${stats['percentile_95']:,.6f}")
        print(f"99th Percentile:     ${stats['percentile_99']:,.6f}")
        
        # Profit/Loss analysis
        pl_analysis = self.analyze_profit_loss()
        print(f"\n{'='*50}")
        print("PROFIT/LOSS BREAKDOWN")
        print(f"{'='*50}")
        print(f"Profitable Transactions: {pl_analysis['profit_transactions']:,} ({pl_analysis['win_rate']:.2f}%)")
        print(f"Loss Transactions:       {pl_analysis['loss_transactions']:,}")
        print(f"Breakeven Transactions:  {pl_analysis['breakeven_transactions']:,}")
        print(f"Total Profit:            ${pl_analysis['total_profit']:,.2f}")
        print(f"Total Loss:              ${pl_analysis['total_loss']:,.2f}")
        print(f"Average Profit:          ${pl_analysis['avg_profit']:,.6f}")
        print(f"Average Loss:            ${pl_analysis['avg_loss']:,.6f}")
        print(f"Largest Profit:          ${pl_analysis['largest_profit']:,.6f}")
        print(f"Largest Loss:            ${pl_analysis['largest_loss']:,.6f}")
        print(f"Profit/Loss Ratio:       {pl_analysis['profit_loss_ratio']:.2f}")
        
        # Time-based analysis
        time_analysis = self.analyze_time_performance()
        print(f"\n{'='*50}")
        print("TIME-BASED PERFORMANCE")
        print(f"{'='*50}")
        
        if time_analysis['daily']:
            daily = time_analysis['daily']
            print(f"Best Day:     {daily['best_day'][0]} (${float(daily['best_day'][1]):,.2f})")
            print(f"Worst Day:    {daily['worst_day'][0]} (${float(daily['worst_day'][1]):,.2f})")
            print(f"Avg Daily:    ${daily['avg_daily_pnl']:,.2f}")
            print(f"Daily Volatility: ${daily['daily_volatility']:,.2f}")
            print(f"Profitable Days: {daily['profitable_days']}/{daily['total_days']} ({daily['profitable_days']/daily['total_days']*100:.1f}%)")
        
        if time_analysis['hourly']:
            hourly = time_analysis['hourly']
            print(f"Best Hour:    {hourly['best_hour'][0]:02d}:00 (${float(hourly['best_hour'][1]):,.2f})")
            print(f"Worst Hour:   {hourly['worst_hour'][0]:02d}:00 (${float(hourly['worst_hour'][1]):,.2f})")
        
        if time_analysis['monthly']:
            monthly = time_analysis['monthly']
            print(f"Best Month:   {monthly['best_month'][0]} (${float(monthly['best_month'][1]):,.2f})")
            print(f"Worst Month:  {monthly['worst_month'][0]} (${float(monthly['worst_month'][1]):,.2f})")
            print(f"Avg Monthly:  ${monthly['avg_monthly_pnl']:,.2f}")
        
        # Transaction type analysis
        type_analysis = self.analyze_transaction_types()
        print(f"\n{'='*50}")
        print("TRANSACTION TYPE ANALYSIS")
        print(f"{'='*50}")
        
        # Sort by total PNL descending
        sorted_types = sorted(type_analysis.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
        
        print(f"{'Type':<40} {'Total PNL':<15} {'Count':<10} {'Avg PNL':<12} {'Contribution':<12}")
        print("-" * 90)
        
        for tx_type, data in sorted_types[:20]:  # Show top 20
            print(f"{tx_type:<40} ${data['total_pnl']:>10,.2f} {data['count']:>8,} ${data['avg_pnl']:>8,.4f} {data['contribution_percent']:>8.2f}%")
        
        if len(sorted_types) > 20:
            print(f"... and {len(sorted_types) - 20} more transaction types")
        
        # Data quality report
        if self.invalid_records:
            print(f"\n{'='*50}")
            print("DATA QUALITY ISSUES")
            print(f"{'='*50}")
            print(f"Invalid records found: {len(self.invalid_records)}")
            print("Sample invalid records:")
            for record in self.invalid_records[:5]:
                print(f"  Row {record['row_number']} in {record['source_file']}: {record['error']}")
        
        # File breakdown
        if len(self.csv_files) > 1:
            print(f"\n{'='*50}")
            print("FILE BREAKDOWN")
            print(f"{'='*50}")
            for csv_file, stats in self.file_stats.items():
                file_data = [r for r in self.data if r['source_file'] == csv_file]
                if file_data:
                    file_pnl = sum(float(r['pnl']) for r in file_data)
                    print(f"{Path(csv_file).name:<30} ${file_pnl:>12,.2f} ({len(file_data):,} records)")
    
    def export_detailed_analysis(self, output_file):
        """Export detailed analysis to JSON file"""
        analysis_data = {
            'metadata': {
                'source_files': self.csv_files,
                'analysis_date': datetime.now().isoformat(),
                'total_records': self.record_count,
                'valid_records': self.valid_pnl_count,
                'invalid_records': len(self.invalid_records)
            },
            'overall_statistics': self.calculate_statistics(),
            'profit_loss_analysis': self.analyze_profit_loss(),
            'time_performance': self.analyze_time_performance(),
            'transaction_type_analysis': self.analyze_transaction_types(),
            'data_quality_issues': self.invalid_records[:100]  # Limit to first 100
        }
        
        # Convert Decimal objects to float for JSON serialization
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        analysis_data = decimal_to_float(analysis_data)
        
        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"\nDetailed analysis exported to: {output_file}")
    
    def export_monthly_csv_report(self, output_file=None):
        """Export monthly breakdown CSV report with revenue categories"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"monthly_pnl_report_{timestamp}.csv"
        
        # Define revenue sources (including all possible revenue event types)
        revenue_sources = ['doghouse', 'lottery', 'pumpup', 'raffle', 'bucket_staking',
                          'suilotto_bucket_interest', 'unihouse_reward', 'gas_rebates',
                          'interest_withdraw', 'liquid-staking']
        
        # Initialize monthly data structure
        monthly_data = OrderedDict()
        
        # Process data by month
        for record in self.data:
            month_key = record['timestamp'].strftime('%Y-%m')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'Pre-Unihouse PNL': Decimal('0'),
                    'Staking PNL': Decimal('0'),
                    'Fee PNL': Decimal('0'),
                    'Referral Fee': Decimal('0')
                }
                # Initialize revenue sources
                for source in revenue_sources:
                    monthly_data[month_key][f'Revenue_{source}'] = Decimal('0')
            
            # Categorize the transaction
            tx_type = record['type']
            pnl = record['pnl']
            
            if tx_type.startswith('Pre-Unihouse:'):
                monthly_data[month_key]['Pre-Unihouse PNL'] += pnl
            elif tx_type == 'Staking Revenue':
                monthly_data[month_key]['Staking PNL'] += pnl
            elif tx_type == 'Fee Revenue':
                monthly_data[month_key]['Fee PNL'] += pnl
            elif tx_type == 'Referral Fee':
                monthly_data[month_key]['Referral Fee'] += pnl
            elif tx_type.startswith('Revenue Event:'):
                # Extract revenue source
                source = tx_type.replace('Revenue Event:', '')
                if source in revenue_sources:
                    monthly_data[month_key][f'Revenue_{source}'] += pnl
        
        # Write CSV file
        with open(output_file, 'w', newline='') as csvfile:
            # Define column headers
            fieldnames = ['Month', 'Pre-Unihouse PNL']
            for source in revenue_sources:
                fieldnames.append(f'Revenue_{source}')
            fieldnames.extend(['Revenue_Total', 'Staking PNL', 'Fee PNL', 'Referral Fee', 'Total PNL'])
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Initialize totals
            totals = {field: Decimal('0') for field in fieldnames if field != 'Month'}
            
            # Write monthly rows
            for month, data in monthly_data.items():
                row = {'Month': month}
                
                # Add main categories
                row['Pre-Unihouse PNL'] = f"{float(data['Pre-Unihouse PNL']):.2f}"
                totals['Pre-Unihouse PNL'] += data['Pre-Unihouse PNL']
                
                # Add revenue sources
                revenue_total = Decimal('0')
                for source in revenue_sources:
                    key = f'Revenue_{source}'
                    value = data.get(key, Decimal('0'))
                    row[key] = f"{float(value):.2f}"
                    revenue_total += value
                    totals[key] += value
                
                # Add revenue total
                row['Revenue_Total'] = f"{float(revenue_total):.2f}"
                totals['Revenue_Total'] += revenue_total
                
                # Add other categories
                row['Staking PNL'] = f"{float(data['Staking PNL']):.2f}"
                row['Fee PNL'] = f"{float(data['Fee PNL']):.2f}"
                row['Referral Fee'] = f"{float(data['Referral Fee']):.2f}"
                
                totals['Staking PNL'] += data['Staking PNL']
                totals['Fee PNL'] += data['Fee PNL']
                totals['Referral Fee'] += data['Referral Fee']
                
                # Calculate total PNL
                total_pnl = (data['Pre-Unihouse PNL'] + revenue_total + 
                            data['Staking PNL'] + data['Fee PNL'] + data['Referral Fee'])
                row['Total PNL'] = f"{float(total_pnl):.2f}"
                totals['Total PNL'] += total_pnl
                
                writer.writerow(row)
            
            # Write totals row
            total_row = {'Month': 'Total'}
            for field in fieldnames[1:]:  # Skip 'Month'
                total_row[field] = f"{float(totals[field]):.2f}"
            writer.writerow(total_row)
        
        print(f"\nMonthly CSV report exported to: {output_file}")
    
    def run_analysis(self, export_json=False, export_monthly_csv=False):
        """Run complete analysis"""
        if not self.load_data():
            return False
        
        if self.valid_pnl_count == 0:
            print("No valid PNL data found!")
            return False
        
        # Generate summary report
        self.generate_summary_report()
        
        # Export detailed analysis if requested
        if export_json:
            base_name = Path(self.csv_files[0]).stem
            output_file = f"{base_name}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.export_detailed_analysis(output_file)
        
        # Export monthly CSV report if requested
        if export_monthly_csv:
            self.export_monthly_csv_report()
        
        return True

def detect_chunk_files():
    """Automatically detect chunk files in the current directory"""
    chunk_patterns = [
        'chunk_*.csv',
        'chunk*.csv',
        '*chunk*.csv',
        'part_*.csv',
        'part*.csv'
    ]
    
    chunk_files = set()  # Use set to avoid duplicates
    for pattern in chunk_patterns:
        files = glob.glob(pattern)
        if files:
            chunk_files.update(files)
    
    # Convert back to list and sort naturally (chunk_1, chunk_2, etc.)
    chunk_files = list(chunk_files)
    chunk_files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', x)])
    
    return chunk_files

def main():
    parser = argparse.ArgumentParser(description='Advanced PNL Analysis Tool - Multi-file Support')
    parser.add_argument('csv_files', nargs='*', 
                       help='CSV files to analyze (supports multiple files)')
    parser.add_argument('--export-json', action='store_true',
                       help='Export detailed analysis to JSON file')
    parser.add_argument('--export-monthly-csv', action='store_true',
                       help='Export monthly breakdown to CSV file')
    parser.add_argument('--auto-chunks', action='store_true',
                       help='Automatically detect and process chunk files')
    parser.add_argument('--version', action='version', version='PNL Analyzer 2.1')
    
    args = parser.parse_args()
    
    # Determine which files to process
    csv_files = []
    
    if args.auto_chunks:
        chunk_files = detect_chunk_files()
        if chunk_files:
            print(f"Auto-detected {len(chunk_files)} chunk files:")
            for i, file in enumerate(chunk_files, 1):
                print(f"  {i}. {file}")
            csv_files = chunk_files
        else:
            print("No chunk files found. Looking for default file...")
    
    if not csv_files:
        if args.csv_files:
            csv_files = args.csv_files
        else:
            # Try default file
            default_file = 'result_2024-06-01_to_2025-06-01_total_2973469.49.csv'
            if Path(default_file).exists():
                csv_files = [default_file]
            else:
                print("No CSV files specified and no default file found.")
                print("Usage:")
                print("  python3 GetTotalPNL.py file1.csv file2.csv  # Analyze specific files")
                print("  python3 GetTotalPNL.py --auto-chunks        # Auto-detect chunk files")
                print("  python3 GetTotalPNL.py                      # Use default file")
                sys.exit(1)
    
    # Validate all files exist
    missing_files = [f for f in csv_files if not Path(f).exists()]
    if missing_files:
        print(f"Error: Files not found: {missing_files}")
        sys.exit(1)
    
    analyzer = PNLAnalyzer(csv_files)
    
    try:
        success = analyzer.run_analysis(export_json=args.export_json, 
                                       export_monthly_csv=args.export_monthly_csv)
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()