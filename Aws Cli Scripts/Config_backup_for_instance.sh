#!/bin/bash

# Log file to store the output
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_FILE="ec2_instance_config_backup_$TIMESTAMP.json"

# Prompt for EC2 instance IDs (comma-separated)
read -p "Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): " INSTANCE_IDS

# Convert comma-separated instance IDs into an array
IFS=',' read -ra INSTANCE_ID_ARRAY <<< "$INSTANCE_IDS"

# Initialize the output file with a JSON structure
echo "{" > "$OUTPUT_FILE"
echo "\"Instances\": [" >> "$OUTPUT_FILE"

# Function to fetch instance details
fetch_instance_details() {
  INSTANCE_ID=$1
  echo "Fetching configuration for instance $INSTANCE_ID"

  # Fetch EC2 instance details
  INSTANCE_DETAILS=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --output json)
  
  if [[ $? -ne 0 || -z "$INSTANCE_DETAILS" ]]; then
    echo "Error fetching instance details for $INSTANCE_ID. Skipping."
    return 1
  fi

  # Append the instance details to the output file
  # Add a comma separator if it's not the first instance
  if [[ "$FIRST_INSTANCE" == "true" ]]; then
    FIRST_INSTANCE="false"
  else
    echo "," >> "$OUTPUT_FILE"
  fi

  echo "$INSTANCE_DETAILS" >> "$OUTPUT_FILE"
}

# Variable to handle comma for JSON formatting
FIRST_INSTANCE="true"

# Loop over each instance ID
for INSTANCE_ID in "${INSTANCE_ID_ARRAY[@]}"; do
  fetch_instance_details "$INSTANCE_ID"
done

# Close the JSON structure
echo "]" >> "$OUTPUT_FILE"
echo "}" >> "$OUTPUT_FILE"

# Output completion message
echo "Configuration backup completed. The details are saved in $OUTPUT_FILE."
