import boto3
import csv

# Input: List of account numbers
account_numbers_input = [
    "123456789764",
    "123456789764",
    "123456789764",
]

# Role to assume in child accounts
role_name = "Switch-account-role"

# List of required tags
required_tags = ['Name', 'Env', 'Grade', 'Application', 'Environment', 'Product']

# Initialize a list to hold all instance details
instances_details = []

# Function to assume role in a target account
def assume_role(account_id, role_name):
    sts_client = boto3.client('sts')
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    assumed_role = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="CrossAccountSession")
    credentials = assumed_role['Credentials']
    return boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

# Iterate through each account
for account_id in account_numbers_input:
    print(f"Processing account: {account_id}")

    # Use the main account credentials for the first account, or assume role for others
    if account_id == boto3.client('sts').get_caller_identity()['Account']:
        session = boto3.Session()  # Use default session for the main account
    else:
        session = assume_role(account_id, role_name)  # Assume role for child accounts

    # Get the list of all available regions
    ec2_client = session.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    # Iterate through each region
    for region in regions:
        print(f"Processing region: {region} in account: {account_id}")
        ec2 = session.client('ec2', region_name=region)

        # Describe instances in the region
        instances = ec2.describe_instances()

        # Extract information about instances
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                # Extract tags dynamically
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}

                # Collect information for the required tags
                instance_tags = {tag: tags.get(tag, 'N/A') for tag in required_tags}

                state = instance['State']['Name']
                launch_time = instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S')
                availability_zone = instance['Placement']['AvailabilityZone']
                private_ip = instance.get('PrivateIpAddress', 'N/A')
                public_ip = instance.get('PublicIpAddress', 'N/A')
                instance_type = instance['InstanceType']
                platform = instance.get('Platform', 'Linux/Unix')  # Default to Linux/Unix if 'Platform' doesn't exist
                key_name = instance.get('KeyName', 'N/A')  # Get the KeyName if present

                # Get state transition reason for stopped instances
                state_transition_reason = instance.get('StateTransitionReason', 'N/A')  # Get the StateTransitionReason if present

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
                    'Account Number': account_id,
                    'Private IP': private_ip,
                    'Instance ID': instance['InstanceId'],
                    'AZ': availability_zone,
                    'Region': region,
                    'State': state,
                    'Public IP': public_ip,
                    'Launchdate': launch_time,
                    'State Transition Reason': state_transition_reason,  # Add state transition reason
                    'Instance Type': instance_type,
                    'OS': platform,
                    'KeyName': key_name,
                    'Volume IDs': volume_ids_info,
                    'Volume Sizes': volume_sizes_info,
                    **instance_tags  # Add dynamic tags to the instance info
                }

                instances_details.append(instance_info)

        print(f"Completed processing region: {region} for account: {account_id}")
    print(f"Completed processing account: {account_id}")

# Create a CSV file with the name 'organization-inventory-withtags.csv'
csv_filename = "organization-inventory-withtags-2.csv"

# Create the CSV file and write the header row
with open(csv_filename, 'w', newline='') as csvfile:
    # Dynamic fieldnames based on required tags
    fieldnames = ['Account Number', 'Private IP', 'Instance ID', 'AZ', 'Region', 'State', 'Public IP', 'Launchdate', 'State Transition Reason', 'Instance Type', 'OS', 'KeyName', 'Volume IDs', 'Volume Sizes'] + required_tags

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Write instance details rows
    for instance in instances_details:
        writer.writerow(instance)

print(f"CSV file '{csv_filename}' has been created successfully.")