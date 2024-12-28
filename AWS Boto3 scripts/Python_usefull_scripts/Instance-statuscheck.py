import boto3

def get_instance_details(instance_ids):
    # Initialize EC2 client
    ec2_client = boto3.client('ec2')

    # Fetch instance details
    try:
        response = ec2_client.describe_instances(InstanceIds=instance_ids)
    except ec2_client.exceptions.ClientError as e:
        print(f"Error fetching instance details: {e}")
        return

    # Print the header
    print(f"{'Instance ID':<20}{'Instance Name':<25}{'Private IP':<15}{'State':<15}{'Instance Type':<15}{'Status Checks (3/3)':<20}")

    # Process each instance in the response
    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instance_id = instance.get('InstanceId', 'N/A')
            private_ip = instance.get('PrivateIpAddress', 'N/A')
            state = instance.get('State', {}).get('Name', 'N/A')
            instance_type = instance.get('InstanceType', 'N/A')

            # Fetch 'Name' tag if available
            tags = instance.get('Tags', [])
            name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), 'N/A')

            # Fetch 3/3 status checks
            try:
                status_response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
                instance_statuses = status_response.get('InstanceStatuses', [])
                if instance_statuses:
                    instance_status = instance_statuses[0]
                    instance_check = instance_status.get('InstanceStatus', {}).get('Status', 'N/A')
                    system_check = instance_status.get('SystemStatus', {}).get('Status', 'N/A')
                    status_checks = f"{instance_check}/{system_check}"
                else:
                    status_checks = "N/A"
            except Exception as e:
                status_checks = f"Error: {e}"

            # Format and print each row
            print(f"{instance_id:<20}{name:<25}{private_ip:<15}{state:<15}{instance_type:<15}{status_checks:<20}")

if __name__ == "__main__":
    # Prompt for EC2 instance IDs (comma-separated)
    instance_ids_input = input("Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): ")
    instance_ids = [instance_id.strip() for instance_id in instance_ids_input.split(",") if instance_id.strip()]

    if not instance_ids:
        print("No instance IDs provided. Exiting.")
    else:
        get_instance_details(instance_ids)