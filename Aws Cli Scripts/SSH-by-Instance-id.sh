#!/bin/bash

# Prompt for the EC2 Instance ID
read -p "Enter the EC2 Instance ID: " INSTANCE_ID

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it and try again."
    exit 1
fi

# Fetch Key Name and Private IP Address using AWS CLI
echo "Fetching details for instance $INSTANCE_ID..."
INSTANCE_DETAILS=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[0].Instances[0].[KeyName, PrivateIpAddress]" --output text 2>/dev/null)

if [[ -z "$INSTANCE_DETAILS" ]]; then
    echo "Error: Could not retrieve details for instance $INSTANCE_ID. Check if the instance ID is correct and you have appropriate permissions."
    exit 1
fi

# Parse the Key Name and Private IP Address
KEY_NAME=$(echo "$INSTANCE_DETAILS" | awk '{print $1}')
PRIVATE_IP=$(echo "$INSTANCE_DETAILS" | awk '{print $2}')

# Validate Key Name and Private IP
if [[ -z "$KEY_NAME" || -z "$PRIVATE_IP" ]]; then
    echo "Error: Missing Key Name or Private IP for instance $INSTANCE_ID. Please check the instance configuration."
    exit 1
fi

echo "Key Name: $KEY_NAME"
echo "Private IP: $PRIVATE_IP"

# Check if the private key file exists
KEY_PATH="$HOME/path/${KEY_NAME}.pem"
if [[ ! -f "$KEY_PATH" ]]; then
    echo "Error: Private key file $KEY_PATH not found. Ensure the key exists in ~/.ssh/."
    exit 1
fi

# Set appropriate permissions for the private key
chmod 400 "$KEY_PATH"

# Initiate SSH connection
echo "Initiating SSH connection to $PRIVATE_IP using key $KEY_PATH..."
ssh -i "$KEY_PATH" ec2-user@"$PRIVATE_IP"
