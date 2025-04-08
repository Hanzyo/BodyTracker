#!/usr/bin/env python3
import os
import sys
import json
import datetime
import argparse
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter, date2num
import matplotlib.ticker as ticker

class MetricsTracker:
    def __init__(self):
        self.data_file = "metrics_data.json"
        self.metrics = {}
        self.load_data()
        
    def load_data(self):
        """Load existing data from file or create empty structure if file doesn't exist"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as file:
                    data = json.load(file)
                    # Convert string dates back to datetime objects
                    self.metrics = {metric: {datetime.datetime.strptime(date, '%Y-%m-%d').date(): value 
                                           for date, value in values.items()}
                                   for metric, values in data.items()}
            except Exception as e:
                print(f"Error loading data: {e}")
                print("Starting with empty data set.")
                self.metrics = {}
        else:
            self.metrics = {}
    
    def save_data(self):
        """Save current data to file"""
        # Convert datetime objects to string for JSON serialization
        serializable_metrics = {
            metric: {date.strftime('%Y-%m-%d'): value for date, value in values.items()}
            for metric, values in self.metrics.items()
        }
        
        try:
            with open(self.data_file, 'w') as file:
                json.dump(serializable_metrics, file, indent=2)
            print(f"Data saved successfully to {self.data_file}")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def record_today(self):
        """Record metrics for today"""
        # Use local timezone
        today = datetime.datetime.now().date()
        day_of_week = today.strftime("%A")
        
        print(f"\n=== Recording metrics for {day_of_week}, {today} ===\n")
        
        # List existing metrics, if any
        if self.metrics:
            print("Current metrics being tracked:")
            for i, metric in enumerate(self.metrics.keys(), 1):
                print(f"{i}. {metric}")
            
        # Ask if user wants to add new metrics
        add_new = input("\nWould you like to add any new metrics to track? (y/n): ").lower().strip()
        if add_new == 'y':
            while True:
                new_metric = input("Enter name of new metric (or press enter to stop adding): ").strip()
                if not new_metric:
                    break
                
                if new_metric not in self.metrics:
                    unit = input(f"What unit is {new_metric} measured in? (e.g., kg, cm): ").strip()
                    metric_with_unit = f"{new_metric} ({unit})" if unit else new_metric
                    self.metrics[metric_with_unit] = {}
                    print(f"Added '{metric_with_unit}' to tracked metrics.")
                else:
                    print(f"'{new_metric}' is already being tracked.")
        
        # Record values for each metric
        if not self.metrics:
            print("\nNo metrics configured. Let's add some first.")
            while True:
                new_metric = input("Enter name of metric to track (or press enter to stop): ").strip()
                if not new_metric:
                    if not self.metrics:
                        print("You must add at least one metric.")
                        continue
                    break
                
                unit = input(f"What unit is {new_metric} measured in? (e.g., kg, cm): ").strip()
                metric_with_unit = f"{new_metric} ({unit})" if unit else new_metric
                self.metrics[metric_with_unit] = {}
                print(f"Added '{metric_with_unit}' to tracked metrics.")
        
        # Now record values for each metric
        print("\nEnter today's values (leave blank to skip):")
        for metric in list(self.metrics.keys()):
            while True:
                try:
                    value_input = input(f"{metric}: ").strip()
                    if not value_input:
                        break
                    
                    value = float(value_input)
                    self.metrics[metric][today] = value
                    break
                except ValueError:
                    print("Please enter a valid number.")
        
        print("\nToday's recording completed.")
    
    def fill_missing_dates(self):
        """Fill missing dates using last known value (forward fill)"""
        if not self.metrics:
            return
            
        # Find the earliest and latest dates across all metrics
        all_dates = [date for metric_data in self.metrics.values() for date in metric_data.keys()]
        if not all_dates:
            return
            
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        # Create a complete date range
        date_range = []
        current_date = min_date
        while current_date <= max_date:
            date_range.append(current_date)
            current_date = current_date + datetime.timedelta(days=1)
        
        # Fill missing dates for each metric
        for metric, values in self.metrics.items():
            filled_values = {}
            last_value = None
            
            for date in date_range:
                if date in values:
                    # We have actual data for this date
                    filled_values[date] = values[date]
                    last_value = values[date]
                elif last_value is not None:
                    # Forward fill with last known value
                    filled_values[date] = last_value
            
            self.metrics[metric] = filled_values
    
    def interpolate_missing_data(self):
        """Linear interpolation of missing data points"""
        for metric, values in self.metrics.items():
            dates = sorted(values.keys())
            if len(dates) < 2:
                continue
                
            # Find gaps that need interpolation
            for i in range(len(dates) - 1):
                start_date = dates[i]
                end_date = dates[i + 1]
                delta = (end_date - start_date).days
                
                # If there's a gap of more than 1 day
                if delta > 1:
                    start_val = values[start_date]
                    end_val = values[end_date]
                    
                    # Calculate interpolation values
                    for j in range(1, delta):
                        interp_date = start_date + datetime.timedelta(days=j)
                        # Linear interpolation
                        ratio = j / delta
                        interp_val = start_val + (end_val - start_val) * ratio
                        values[interp_date] = interp_val
    
    def visualize(self):
        """Create visualization of recorded metrics"""
        if not self.metrics:
            print("No data available to visualize.")
            return
            
        # Apply data filling/interpolation
        self.fill_missing_dates()
        
        # Prepare data for plotting
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Find all unique dates across all metrics
        all_dates = set()
        for values in self.metrics.values():
            all_dates.update(values.keys())
        
        if not all_dates:
            print("No data points available to plot.")
            return
            
        # Calculate the date range
        min_date = min(all_dates)
        max_date = max(all_dates)
        date_range = (max_date - min_date).days
        
        # Map each metric to a color to ensure consistent coloring
        colors = plt.cm.tab10.colors
        metric_colors = {metric: colors[i % len(colors)] for i, metric in enumerate(self.metrics.keys())}
        
        for metric, values in self.metrics.items():
            if not values:
                continue
                
            dates = sorted(values.keys())
            if not dates:
                continue
                
            # Convert datetime.date to matplotlib dates (float values)
            plot_dates = [date2num(date) for date in dates]
            measurements = [values[date] for date in dates]
            
            # Plot the data
            line, = ax.plot(plot_dates, measurements, 'o-', label=metric, color=metric_colors[metric])
            
            # Add data points
            for date_num, value, date in zip(plot_dates, measurements, dates):
                ax.annotate(f'{value:.1f}', (date_num, value), fontsize=8, 
                           xytext=(0, 5), textcoords='offset points', ha='center')
        
        # Dynamic x-axis range adjustment based on data points
        if date_range == 0:  # Only one day of data
            # Add padding of 3 days before and after the single date
            ax.set_xlim(date2num(min_date - datetime.timedelta(days=3)), 
                       date2num(max_date + datetime.timedelta(days=3)))
        elif date_range < 7:  # Less than a week of data
            # Add padding of 1 day before and after
            ax.set_xlim(date2num(min_date - datetime.timedelta(days=1)), 
                       date2num(max_date + datetime.timedelta(days=1)))
        elif date_range < 30:  # Less than a month
            # Add padding of 2 days
            ax.set_xlim(date2num(min_date - datetime.timedelta(days=2)), 
                       date2num(max_date + datetime.timedelta(days=2)))
        else:
            # For longer periods, add padding of 5% of the range
            padding = datetime.timedelta(days=max(int(date_range * 0.05), 3))
            ax.set_xlim(date2num(min_date - padding), date2num(max_date + padding))
        
        # Formatting
        fig.autofmt_xdate()
        
        # Adjust date formatter based on range
        if date_range <= 14:
            date_format = DateFormatter("%b %d\n%a")  # Month day, Day of week
        elif date_range <= 180:
            date_format = DateFormatter("%b %d")  # Month day
        else:
            date_format = DateFormatter("%b %Y")  # Month Year
            
        ax.xaxis.set_major_formatter(date_format)
        
        # Determine appropriate date tick interval based on date range
        if date_range == 0:
            # Only one day, show just that day
            ax.xaxis.set_major_locator(ticker.FixedLocator([date2num(min_date)]))
        elif date_range <= 7:
            # For a week or less, show all days
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=date_range+1))
        elif date_range <= 30:
            # For up to a month, show weekly ticks
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=max(date_range//7+1, 4)))
        elif date_range <= 365:
            # For up to a year, show monthly ticks
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=max(date_range//30+1, 4)))
        else:
            # For very long periods, show quarterly ticks
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=max(date_range//90+1, 4)))
        
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_title('Metrics Tracker', fontsize=16)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Measurement', fontsize=12)
        
        # Create a proper legend with metric names
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.tight_layout()
        plt.show()

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Metrics Tracker')
    parser.add_argument('-g', '--graph-only', action='store_true', 
                        help='Only display the graph without recording new data')
    args = parser.parse_args()
    
    tracker = MetricsTracker()
    
    try:
        if not args.graph_only:
            tracker.record_today()
            tracker.save_data()
        
        tracker.visualize()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Saving data...")
        if not args.graph_only:
            tracker.save_data()
        sys.exit(0)

if __name__ == "__main__":
    main()