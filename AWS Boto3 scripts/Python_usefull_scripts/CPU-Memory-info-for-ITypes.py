import boto3
import csv
#this files will fetch all memory cpu inventory for all the instance types
# Read instance types from a text file
def read_instance_types(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Initialize the EC2 client
ec2 = boto3.client('ec2')

# Path to the text file with instance types
instance_types_file = 'instance_types.txt'

# Get instance types from the text file
instance_types = read_instance_types(instance_types_file)

# Create a list to hold instances details
instances_details = []

# Fetch instance type details
for instance_type in instance_types:
    instance_info = ec2.describe_instance_types(InstanceTypes=[instance_type])['InstanceTypes'][0]
    vcpus = instance_info['VCpuInfo']['DefaultVCpus']
    memory_gib = instance_info['MemoryInfo']['SizeInMiB'] / 1024  # Convert MiB to GiB
    
    instance_detail = {
        'Instance Type': instance_type,
        'CPU Capacity': vcpus,
        'Memory Capacity (GiB)': memory_gib
    }
    
    instances_details.append(instance_detail)

# Create a CSV file and write the header row
output_file = 'instance_capacity_details.csv'
with open(output_file, 'w', newline='') as csvfile:
    fieldnames = ['Instance Type', 'CPU Capacity', 'Memory Capacity (GiB)']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Write instance details rows
    for instance in instances_details:
        writer.writerow(instance)

print(f"CSV file '{output_file}' has been created successfully.")
