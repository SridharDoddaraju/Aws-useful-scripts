#!/bin/bash

# Log file to store the output
LOG_FILE="ec2_instance_config_backup_$(date +%Y-%m-%d_%H-%M-%S).log"

# Prompt for EC2 instance IDs (comma-separated)
read -p "Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): " INSTANCE_IDS

# Convert comma-separated instance IDs into an array
IFS=',' read -ra INSTANCE_ID_ARRAY <<< "$INSTANCE_IDS"

# Initialize the backup JSON structure
CONFIG_BACKUP_JSON="{\"Instances\":[]}"

# Function to fetch instance and volume details
fetch_instance_details() {
  INSTANCE_ID=$1
  echo "Fetching configuration for instance $INSTANCE_ID" | tee -a "$LOG_FILE"

  # Fetch EC2 instance details
  INSTANCE_DETAILS=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[*].Instances[*].{ID:InstanceId,Type:InstanceType,AMI:ImageId,SG:SecurityGroups,Subnet:SubnetId,VPC:VpcId,Role:IamInstanceProfile,Key:KeyName,ElasticIP:PublicIpAddress}" --output json)
  
  if [[ $? -ne 0 || -z "$INSTANCE_DETAILS" ]]; then
    echo "Error fetching instance details for $INSTANCE_ID. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
    return 1
  fi

  # Fetch volume details
  VOLUME_DETAILS=$(aws ec2 describe-volumes --filters Name=attachment.instance-id,Values="$INSTANCE_ID" --query "Volumes[*].{ID:VolumeId,Size:Size,Type:VolumeType,Device:Attachments[0].Device}" --output json)

  if [[ $? -ne 0 || -z "$VOLUME_DETAILS" ]]; then
    echo "Error fetching volume details for $INSTANCE_ID. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
    return 1
  fi

  # Fetch instance tags
  INSTANCE_TAGS=$(aws ec2 describe-tags --filters Name=resource-id,Values="$INSTANCE_ID" --output json)
  if [[ $? -ne 0 || -z "$INSTANCE_TAGS" ]]; then
    echo "Error fetching tags for instance $INSTANCE_ID. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
    return 1
  fi

  # Add instance details to the backup JSON structure
  CONFIG_BACKUP_JSON=$(echo "$CONFIG_BACKUP_JSON" | jq ".Instances += [{\"InstanceID\": \"$INSTANCE_ID\", \"Details\": $INSTANCE_DETAILS, \"Volumes\": $VOLUME_DETAILS, \"InstanceTags\": $INSTANCE_TAGS}]")
}

# Loop over each instance ID
for INSTANCE_ID in "${INSTANCE_ID_ARRAY[@]}"; do
  fetch_instance_details "$INSTANCE_ID"
done

# Save the final JSON to a file
echo "$CONFIG_BACKUP_JSON" | jq . > "ec2_instance_config_backup.json"

# Output completion message
echo "Configuration backup completed. The details are saved in ec2_instance_config_backup.json."
echo "Check $LOG_FILE for log details."
