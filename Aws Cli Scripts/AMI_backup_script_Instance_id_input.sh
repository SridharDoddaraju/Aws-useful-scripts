#!/bin/bash

# Log file (update the path as needed)
LOG_FILE="/var/log/ami_backup.log"

# Ensure the log file exists and is writable
touch "$LOG_FILE"
if [[ ! -w "$LOG_FILE" ]]; then
  echo "Error: Cannot write to log file at $LOG_FILE. Please check permissions."
  exit 1
fi

# Prompt for EC2 instance IDs (comma-separated)
read -p "Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): " INSTANCE_IDS

# Convert comma-separated instance IDs into an array
IFS=',' read -ra INSTANCE_ID_ARRAY <<< "$INSTANCE_IDS"

# Check if any instance IDs were provided
if [[ ${#INSTANCE_ID_ARRAY[@]} -eq 0 ]]; then
  echo "No instance IDs provided. Exiting." | tee -a "$LOG_FILE"
  exit 1
fi

# Validate and filter valid instance IDs
VALID_INSTANCE_IDS=()
for INSTANCE_ID in "${INSTANCE_ID_ARRAY[@]}"; do
  INSTANCE_CHECK=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[*].Instances[*].InstanceId" --output text 2>/dev/null)
  if [[ -n "$INSTANCE_CHECK" ]]; then
    VALID_INSTANCE_IDS+=("$INSTANCE_ID")
  else
    echo "Warning: Instance ID $INSTANCE_ID is invalid or not found. Skipping." | tee -a "$LOG_FILE"
  fi
done

# Check if there are valid instance IDs to process
if [[ ${#VALID_INSTANCE_IDS[@]} -eq 0 ]]; then
  echo "No valid instance IDs found. Exiting." | tee -a "$LOG_FILE"
  exit 1
fi

# Process each valid instance to create AMI backups
for INSTANCE_ID in "${VALID_INSTANCE_IDS[@]}"; do
  echo "Processing instance $INSTANCE_ID..." | tee -a "$LOG_FILE"

  # Get all tags from the instance
  INSTANCE_TAGS=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[0].Instances[0].Tags" --output json 2>/dev/null)
  if [[ -z "$INSTANCE_TAGS" || "$INSTANCE_TAGS" == "None" ]]; then
    echo "Warning: No tags found for instance $INSTANCE_ID. Continuing without tags." | tee -a "$LOG_FILE"
    INSTANCE_TAGS="[]"
  fi

  # Create AMI backup
  AMI_NAME="AMI-backup-$(date +%Y-%m-%d)"
  echo "Creating AMI for instance $INSTANCE_ID with name $AMI_NAME..." | tee -a "$LOG_FILE"
  AMI_ID=$(aws ec2 create-image --instance-id "$INSTANCE_ID" --name "$AMI_NAME" --no-reboot --query "ImageId" --output text 2>/dev/null)

  if [[ $? -ne 0 || -z "$AMI_ID" ]]; then
    echo "Error: Failed to create AMI for instance $INSTANCE_ID. Skipping." | tee -a "$LOG_FILE"
    continue
  fi

  # Tag the AMI with all instance tags
  echo "Tagging AMI $AMI_ID with instance tags..." | tee -a "$LOG_FILE"
  aws ec2 create-tags --resources "$AMI_ID" --tags "$INSTANCE_TAGS" 2>/dev/null

  if [[ $? -ne 0 ]]; then
    echo "Error: Failed to tag AMI $AMI_ID with instance tags. Continuing..." | tee -a "$LOG_FILE"
  else
    echo "Successfully tagged AMI $AMI_ID with instance tags." | tee -a "$LOG_FILE"
  fi

  # Retrieve snapshots associated with the AMI
  echo "Retrieving snapshots associated with AMI $AMI_ID..." | tee -a "$LOG_FILE"
  SNAPSHOT_IDS=$(aws ec2 describe-images --image-ids "$AMI_ID" --query "Images[0].BlockDeviceMappings[*].Ebs.SnapshotId" --output text 2>/dev/null)

  if [[ -z "$SNAPSHOT_IDS" ]]; then
    echo "Warning: No snapshots found for AMI $AMI_ID. Skipping snapshot tagging." | tee -a "$LOG_FILE"
    continue
  fi

  # Tag each snapshot with instance tags
  for SNAPSHOT_ID in $SNAPSHOT_IDS; do
    echo "Tagging snapshot $SNAPSHOT_ID with instance tags..." | tee -a "$LOG_FILE"
    aws ec2 create-tags --resources "$SNAPSHOT_ID" --tags "$INSTANCE_TAGS" 2>/dev/null
    if [[ $? -eq 0 ]]; then
      echo "Successfully tagged snapshot $SNAPSHOT_ID with instance tags." | tee -a "$LOG_FILE"
    else
      echo "Error: Failed to tag snapshot $SNAPSHOT_ID with instance tags." | tee -a "$LOG_FILE"
    fi
  done
done

# Print completion message
echo "All AMI backup and tagging operations have been completed. Check $LOG_FILE for details." | tee -a "$LOG_FILE"