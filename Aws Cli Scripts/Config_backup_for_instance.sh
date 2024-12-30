#!/bin/bash

# Log file to store the output
LOG_FILE="ec2_instance_config_backup_$(date +%Y-%m-%d_%H-%M-%S).log"

# Prompt for EC2 instance IDs (comma-separated)
read -p "Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): " INSTANCE_IDS

# Convert comma-separated instance IDs into an array
IFS=',' read -ra INSTANCE_ID_ARRAY <<< "$INSTANCE_IDS"

# Initialize the backup JSON structure
CONFIG_BACKUP_JSON="{\"Instances\":[]}"

# Function to fetch instance details
fetch_instance_details() {
  INSTANCE_ID=$1
  echo "Fetching configuration for instance $INSTANCE_ID" | tee -a "$LOG_FILE"

  # Fetch EC2 instance details
  INSTANCE_DETAILS=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --output json)
  
  if [[ $? -ne 0 || -z "$INSTANCE_DETAILS" ]]; then
    echo "Error fetching instance details for $INSTANCE_ID. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
    return 1
  fi

  # Add instance details to the backup JSON structure
  CONFIG_BACKUP_JSON=$(echo "$CONFIG_BACKUP_JSON" | jq ".Instances += [{\"InstanceID\": \"$INSTANCE_ID\", \"Details\": $INSTANCE_DETAILS}]")
}

# Loop over each instance ID
for INSTANCE_ID in "${INSTANCE_ID_ARRAY[@]}"; do
  fetch_instance_details "$INSTANCE_ID"
done

# Add timestamp to output file name
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_FILE="ec2_instance_config_backup_$TIMESTAMP.json"

# Save the final JSON to a file with timestamp
echo "$CONFIG_BACKUP_JSON" | jq . > "$OUTPUT_FILE"

# Output completion message
echo "Configuration backup completed. The details are saved in $OUTPUT_FILE."
echo "Check $LOG_FILE for log details."
