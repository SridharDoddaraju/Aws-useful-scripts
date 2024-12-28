#!/bin/bash

# Prompt for EC2 instance IDs (comma-separated)
read -p "Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): " INSTANCE_IDS

# Convert comma-separated instance IDs into an array
IFS=',' read -ra INSTANCE_ID_ARRAY <<< "$INSTANCE_IDS"

# Check if any instance IDs were provided
if [[ ${#INSTANCE_ID_ARRAY[@]} -eq 0 ]]; then
  echo "No instance IDs provided. Exiting."
  exit 1
fi

# Validate and filter valid instance IDs
VALID_INSTANCE_IDS=()
for INSTANCE_ID in "${INSTANCE_ID_ARRAY[@]}"; do
  INSTANCE_CHECK=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[*].Instances[*].InstanceId" --output text 2>/dev/null)
  if [[ -n "$INSTANCE_CHECK" ]]; then
    VALID_INSTANCE_IDS+=("$INSTANCE_ID")
  else
    echo "Warning: Instance ID $INSTANCE_ID is invalid or not found. Skipping."
  fi
done

# Check if there are valid instance IDs to process
if [[ ${#VALID_INSTANCE_IDS[@]} -eq 0 ]]; then
  echo "No valid instance IDs found. Exiting."
  exit 1
fi

# Log file (update the path as needed)
LOG_FILE="/path/to/log_file.log"

# Process each valid instance to create AMI backups
for INSTANCE_ID in "${VALID_INSTANCE_IDS[@]}"; do
  # Get the instance name from tags, default to "Unnamed-Instance" if no name found
  INSTANCE_NAME=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[0].Instances[0].Tags[?Key=='Name'].Value" --output text)
  if [[ -z "$INSTANCE_NAME" ]]; then
    INSTANCE_NAME="Unnamed-Instance"
  fi

  # Define AMI name using instance name and current date
  AMI_NAME="${INSTANCE_NAME}-backup-$(date +%Y-%m-%d)"

  # Create AMI backup
  AMI_ID=$(aws ec2 create-image --instance-id "$INSTANCE_ID" --name "$AMI_NAME" --no-reboot --output text)
  if [[ $? -ne 0 || -z "$AMI_ID" ]]; then
    echo "Error creating AMI backup for $INSTANCE_ID. Skipping to next instance." | tee -a "$LOG_FILE"
    continue  # Skip to the next instance if AMI creation fails
  fi

  # Log success
  echo "AMI backup created for instance $INSTANCE_ID with AMI ID: $AMI_ID" | tee -a "$LOG_FILE"
done

# Print completion message
echo "All AMI backup operations have been completed." | tee -a "$LOG_FILE"