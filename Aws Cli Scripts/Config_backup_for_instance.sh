#!/bin/bash

# Prompt for EC2 instance IDs (comma-separated)
read -p "Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): " INSTANCE_IDS

# Convert comma-separated instance IDs into an array
IFS=',' read -ra INSTANCE_ID_ARRAY <<< "$INSTANCE_IDS"

# Loop over each instance ID
for INSTANCE_ID in "${INSTANCE_ID_ARRAY[@]}"; do
  # Fetch the instance name by querying tags (assuming 'Name' tag is set)
  INSTANCE_NAME=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=Name" --query "Tags[0].Value" --output text)

  # If no name tag found, use the instance ID as the name
  if [ "$INSTANCE_NAME" == "None" ]; then
    INSTANCE_NAME="$INSTANCE_ID"
  fi

  # Fetch full instance details
  INSTANCE_DETAILS=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --output json)

  # Save the output to a JSON file with instance name and ID
  BACKUP_FILE="${INSTANCE_NAME}-${INSTANCE_ID}.json"

  # Write the output to the backup file
  echo "$INSTANCE_DETAILS" > "$BACKUP_FILE"

  # Output message
  echo "Backup for instance $INSTANCE_ID saved as $BACKUP_FILE."
done
