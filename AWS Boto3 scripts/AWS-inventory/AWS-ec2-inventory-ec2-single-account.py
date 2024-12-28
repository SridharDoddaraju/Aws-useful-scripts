import boto3
import csv
import os

# Initialize the EC2 client
ec2 = boto3.client('ec2')

# Get the list of all available regions
regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]

# Initialize a set to hold account numbers (to ensure unique account numbers)
account_numbers = set()

# Create a list to hold instances details
instances_details = []

# Iterate through each region
for region in regions:
    ec2 = boto3.client('ec2', region_name=region)
    
    # Describe instances in the region
    instances = ec2.describe_instances(
        Filters=[
           # {'Name': 'tag:Grade', 'Values': ['prod']},  # Uncomment this if you want to filter by 'Grade=prod'
           # {'Name': 'instance-state-name', 'Values': ['running']}  # Uncomment this if you want to filter only running instances
        ]
    )
    
    # Extract information about instances
    for reservation in instances['Reservations']:
        account_number = reservation['OwnerId']  # Get the account number
        account_numbers.add(account_number)  # Add the account number to the set (to ensure we handle multiple regions)
        
        for instance in reservation['Instances']:
            role = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Role'), '')
            name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), '')
            grade = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Grade'), 'N/A')  # Get the Grade tag
            env = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Env'), 'N/A')  # Get the Env tag
            state = instance['State']['Name']
            state_transition_reason = instance.get('StateTransitionReason', 'N/A')  # Get the StateTransitionReason if present
            launch_time = instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S')
            availability_zone = instance['Placement']['AvailabilityZone']
            private_ip = instance.get('PrivateIpAddress', '')
            public_ip = instance.get('PublicIpAddress', '')
            instance_type = instance['InstanceType']
            platform = instance.get('Platform', 'Linux/Unix')  # Get OS, defaulting to Linux/Unix if 'Platform' doesn't exist
            key_name = instance.get('KeyName', 'N/A')  # Get the KeyName if present
            
            # Describe volumes attached to the instance
            volume_details = ec2.describe_volumes(
                Filters=[
                    {'Name': 'attachment.instance-id', 'Values': [instance['InstanceId']]}
                ]
            )
            
            volume_ids = []
            volume_sizes = []
            for volume in volume_details['Volumes']:
                volume_ids.append(volume['VolumeId'])
                volume_sizes.append(str(volume['Size']) + 'GiB')
            
            volume_ids_info = ", ".join(volume_ids)
            volume_sizes_info = ", ".join(volume_sizes)
            
            instance_info = {
                'Account Number': account_number,
                'Role': role,
                'Instance Name': name,
                'Grade': grade,  # Add Grade tag
                'Env': env,  # Add Env tag
                'Private IP': private_ip,
                'Instance ID': instance['InstanceId'],
                'AZ': availability_zone,
                'Region': region,  # Add Region
                'State': state,
                'State Transition Reason': state_transition_reason,  # Add StateTransitionReason
                'Public IP': public_ip,
                'Launchdate': launch_time,
                'Instance Type': instance_type,
                'OS': platform,  # Operating system (OS)
                'KeyName': key_name,  # Add KeyName
                'Volume IDs': volume_ids_info,
                'Volume Sizes': volume_sizes_info
            }
            
            instances_details.append(instance_info)

# Use the first account number for naming the file (assuming all instances belong to the same account)
account_number = next(iter(account_numbers), 'unknown')

# Create a CSV file with the name 'accountnumber-inventory.csv'
csv_filename = f"{account_number}-inventory.csv"

# Create the CSV file and write the header row
with open(csv_filename, 'w', newline='') as csvfile:
    fieldnames = ['Account Number', 'Role', 'Instance Name', 'Grade', 'Env', 'Private IP', 'Instance ID', 'AZ', 'Region', 'State', 'State Transition Reason', 'Public IP', 'Launchdate', 'Instance Type', 'OS', 'KeyName', 'Volume IDs', 'Volume Sizes']

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Write instance details rows
    for instance in instances_details:
        writer.writerow(instance)

print(f"CSV file '{csv_filename}' has been created successfully.")