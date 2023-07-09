#!/bin/bash

# Check if command is provided as argument
if [ $# -eq 0 ]; then
  echo "Error: Please provide a command as an argument."
  exit 1
fi

# Execute the command in the background
$@ &
pid=$!

# Wait for the command to complete
wait $pid

# Get resource usage using 'ps' command
max_rss=$(ps -o rss= -p $pid)
cpu_time=$(ps -o time= -p $pid)

# Convert CPU time to seconds (format: HH:MM:SS)
IFS=':' read -ra time_parts <<< "$cpu_time"
seconds=$((10#${time_parts[0]} * 3600 + 10#${time_parts[1]} * 60 + 10#${time_parts[2]}))

# Display the resource usage
echo "Resource Usage for '$@':"
echo "Max RSS: $max_rss KB"
echo "CPU Time: $seconds seconds"
