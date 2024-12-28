import boto3
import csv

# Input: List of account numbers
account_numbers_input = [
    "123456789764",
    "123456789764",
    "123456789764",
]

# Role to assume in child accounts
role_name = "Role-Name-Accross-accounts"

# List of required tags
required_tags = ['Name', 'Env', 'Grade', 'Application', 'Environment', 'Product']

# Initialize a list to hold all RDS instance details
rds_details = []

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
    # Use the main account credentials for the first account, or assume role for others
    if account_id == boto3.client('sts').get_caller_identity()['Account']:
        session = boto3.Session()  # Use default session for the main account
    else:
        session = assume_role(account_id, role_name)  # Assume role for child accounts

    print(f"Processing account: {account_id}")

    # Get the list of all available regions
    ec2_client = session.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    # Iterate through each region
    for region in regions:
        print(f"Processing region: {region} for account: {account_id}")
        rds = session.client('rds', region_name=region)

        # Describe DB instances in the region
        instances = rds.describe_db_instances()

        # Extract information about each RDS instance
        for instance in instances['DBInstances']:
            db_instance_id = instance['DBInstanceIdentifier']
            db_engine = instance['Engine']
            db_engine_version = instance['EngineVersion']
            db_class = instance['DBInstanceClass']
            db_status = instance['DBInstanceStatus']
            db_region = region
            db_az = instance['AvailabilityZone']
            db_storage = str(instance['AllocatedStorage']) + 'GiB'
            db_endpoint = instance.get('Endpoint', {}).get('Address', 'N/A')  # Handle missing Address
            db_vpc = instance['DBSubnetGroup']['VpcId']
            db_create_time = instance['InstanceCreateTime'].strftime('%Y-%m-%d %H:%M:%S')

            # Log missing endpoint addresses
            if db_endpoint == 'N/A':
                print(f"Endpoint Address missing for DBInstanceIdentifier: {db_instance_id}")

            # Describe tags for the instance
            tags_response = rds.list_tags_for_resource(ResourceName=instance['DBInstanceArn'])
            tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}

            # Collect information for the required tags
            instance_tags = {tag: tags.get(tag, 'N/A') for tag in required_tags}

            # Create a dictionary for the instance details
            instance_info = {
                'Account Number': account_id,
                'DBInstanceIdentifier': db_instance_id,
                'Engine': db_engine,
                'Engine Version': db_engine_version,
                'DB Class': db_class,
                'Status': db_status,
                'Region': db_region,
                'AZ': db_az,
                'Storage': db_storage,
                'Endpoint': db_endpoint,
                'VPC': db_vpc,
                'Creation Time': db_create_time,
                **instance_tags  # Add dynamic tags to the instance info
            }

            rds_details.append(instance_info)

    print(f"Completed processing account: {account_id}")

# Create a CSV file with the name 'organization-rds-inventory.csv'
csv_filename = "organization-rds-inventory-2.csv"

# Create the CSV file and write the header row
with open(csv_filename, 'w', newline='') as csvfile:
    # Dynamic fieldnames based on required tags
    fieldnames = ['Account Number', 'DBInstanceIdentifier', 'Engine', 'Engine Version', 'DB Class', 'Status', 'Region', 'AZ', 'Storage', 'Endpoint', 'VPC', 'Creation Time'] + required_tags

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Write RDS details rows
    for instance in rds_details:
        writer.writerow(instance)

print(f"CSV file '{csv_filename}' has been created successfully.")