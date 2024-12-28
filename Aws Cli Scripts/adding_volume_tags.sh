#!/bin/bash

# Log file to store the output
LOG_FILE="ec2_volume_tag_log_$(date +%Y-%m-%d_%H-%M-%S).log"

# Prompt for EC2 instance IDs (comma-separated)
read -p "Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): " INSTANCE_IDS

# Convert comma-separated instance IDs into an array
IFS=',' read -ra INSTANCE_ID_ARRAY <<< "$INSTANCE_IDS"

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

# Check if there are valid instance IDs
if [[ ${#VALID_INSTANCE_IDS[@]} -eq 0 ]]; then
  echo "No valid instance IDs found. Exiting." | tee -a "$LOG_FILE"
  exit 1
fi

# Process each valid instance
for INSTANCE_ID in "${VALID_INSTANCE_IDS[@]}"; do
  echo "Processing instance: $INSTANCE_ID" | tee -a "$LOG_FILE"

  # Fetch attached volumes for the instance
  VOLUME_DETAILS=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[0].Instances[0].BlockDeviceMappings[*].{DeviceName:DeviceName,VolumeId:Ebs.VolumeId}" --output json)

  # Check if volumes are attached
  if [[ -z "$VOLUME_DETAILS" || "$VOLUME_DETAILS" == "null" ]]; then
    echo "No volumes attached to instance $INSTANCE_ID. Skipping." | tee -a "$LOG_FILE"
    continue
  fi

  # Process each attached volume
  echo "$VOLUME_DETAILS" | jq -c '.[]' | while read -r VOLUME; do
    DEVICE_NAME=$(echo "$VOLUME" | jq -r '.DeviceName')
    VOLUME_ID=$(echo "$VOLUME" | jq -r '.VolumeId')

    if [[ -n "$DEVICE_NAME" && -n "$VOLUME_ID" ]]; then
      echo "Adding tags to volume $VOLUME_ID with device name $DEVICE_NAME" | tee -a "$LOG_FILE"

      # Add Device_Name tag to the volume
      aws ec2 create-tags --resources "$VOLUME_ID" --tags Key=Device_Name,Value="$DEVICE_NAME" 2>/dev/null
      if [[ $? -eq 0 ]]; then
        echo "Device_Name tag added successfully to volume $VOLUME_ID" | tee -a "$LOG_FILE"
      else
        echo "Error adding Device_Name tag to volume $VOLUME_ID" | tee -a "$LOG_FILE"
      fi

      # Add Project_CSI tag to the volume
      aws ec2 create-tags --resources "$VOLUME_ID" --tags Key=Project_CSI,Value=Yes 2>/dev/null
      if [[ $? -eq 0 ]]; then
        echo "Project_CSI tag added successfully to volume $VOLUME_ID" | tee -a "$LOG_FILE"
      else
        echo "Error adding Project_CSI tag to volume $VOLUME_ID" | tee -a "$LOG_FILE"
      fi
    else
      echo "Invalid data for volume or device name. Skipping." | tee -a "$LOG_FILE"
    fi
  done

done

echo "Script execution completed. Check $LOG_FILE for details."
