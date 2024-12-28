import boto3
import csv
from botocore.exceptions import ClientError
from botocore.config import Config

def get_name_tag(tags):
    """Helper function to get the 'Name' tag from a list of tags."""
    for tag in tags:
        if tag['Key'] == 'Name':
            return tag['Value']
    return None

def get_vpc_details_in_region(region_name):
    ec2 = boto3.client('ec2', region_name=region_name)
    
    try:
        # Fetch all VPCs in the region
        vpcs_response = ec2.describe_vpcs()
        vpcs = vpcs_response['Vpcs']
        
        if not vpcs:
            return []  # No VPCs in this region

        region_vpc_details = []

        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            vpc_name = get_name_tag(vpc.get('Tags', []))
            print(f"Fetching details for VPC {vpc_id} in region {region_name}...")

            # Fetch Subnets associated with the VPC
            subnets_response = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            subnets = [{
                'ResourceType': 'Subnet',
                'ResourceId': subnet['SubnetId'],
                'ResourceName': get_name_tag(subnet.get('Tags', []))
            } for subnet in subnets_response['Subnets']]

            # Fetch Route Tables associated with the VPC
            route_tables_response = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            route_tables = [{
                'ResourceType': 'RouteTable',
                'ResourceId': rt['RouteTableId'],
                'ResourceName': get_name_tag(rt.get('Tags', []))
            } for rt in route_tables_response['RouteTables']]

            # Fetch Internet Gateways associated with the VPC
            igw_response = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
            igws = [{
                'ResourceType': 'InternetGateway',
                'ResourceId': igw['InternetGatewayId'],
                'ResourceName': get_name_tag(igw.get('Tags', []))
            } for igw in igw_response['InternetGateways']]

            # Fetch Security Groups associated with the VPC
            security_groups_response = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            security_groups = [{
                'ResourceType': 'SecurityGroup',
                'ResourceId': sg['GroupId'],
                'ResourceName': sg['GroupName']  # Security Groups usually have a GroupName instead of a Name tag
            } for sg in security_groups_response['SecurityGroups']]

            # Fetch EC2 Instances associated with the VPC
            instances_response = ec2.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            instances = []
            for reservation in instances_response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'ResourceType': 'EC2Instance',
                        'ResourceId': instance['InstanceId'],
                        'ResourceName': get_name_tag(instance.get('Tags', []))
                    })

            # Fetch Network ACLs associated with the VPC
            nacls_response = ec2.describe_network_acls(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            nacls = [{
                'ResourceType': 'NetworkAcl',
                'ResourceId': nacl['NetworkAclId'],
                'ResourceName': get_name_tag(nacl.get('Tags', []))
            } for nacl in nacls_response['NetworkAcls']]

            # Fetch VPC Peering Connections
            peering_connections_response = ec2.describe_vpc_peering_connections(Filters=[{'Name': 'requester-vpc-info.vpc-id', 'Values': [vpc_id]}])
            peering_connections = [{
                'ResourceType': 'VpcPeeringConnection',
                'ResourceId': pc['VpcPeeringConnectionId'],
                'ResourceName': get_name_tag(pc.get('Tags', []))
            } for pc in peering_connections_response['VpcPeeringConnections']]

            # Fetch NAT Gateways associated with the VPC
            nat_gateways_response = ec2.describe_nat_gateways(Filter=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            nat_gateways = [{
                'ResourceType': 'NatGateway',
                'ResourceId': ng['NatGatewayId'],
                'ResourceName': get_name_tag(ng.get('Tags', []))
            } for ng in nat_gateways_response['NatGateways']]

            # Fetch Endpoints associated with the VPC
            endpoints_response = ec2.describe_vpc_endpoints(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            endpoints = [{
                'ResourceType': 'VpcEndpoint',
                'ResourceId': ep['VpcEndpointId'],
                'ResourceName': get_name_tag(ep.get('Tags', []))
            } for ep in endpoints_response['VpcEndpoints']]

            resources = subnets + route_tables + igws + security_groups + instances + nacls + peering_connections + nat_gateways + endpoints

            for resource in resources:
                region_vpc_details.append({
                    'Region': region_name,
                    'VpcId': vpc_id,
                    'VpcName': vpc_name,
                    'ResourceType': resource['ResourceType'],
                    'ResourceId': resource['ResourceId'],
                    'ResourceName': resource['ResourceName']
                })

        return region_vpc_details

    except ClientError as e:
        print(f"An error occurred in region {region_name}: {e}")
        return []

def get_vpc_details_across_regions():
    ec2 = boto3.client('ec2')
    regions_response = ec2.describe_regions()
    regions = [region['RegionName'] for region in regions_response['Regions']]

    all_vpc_details = []
    for region in regions:
        region_vpc_details = get_vpc_details_in_region(region)
        if region_vpc_details:
            all_vpc_details.extend(region_vpc_details)

    return all_vpc_details

def write_vpc_details_to_csv(vpc_details, file_name='vpc_details.csv'):
    if not vpc_details:
        print("No VPC details to write.")
        return
    
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Region', 'VpcId', 'VpcName', 'ResourceType', 'ResourceId', 'ResourceName'])

        for vpc in vpc_details:
            writer.writerow([
                vpc['Region'], 
                vpc['VpcId'], 
                vpc['VpcName'], 
                vpc['ResourceType'], 
                vpc['ResourceId'], 
                vpc['ResourceName']
            ])

if __name__ == '__main__':
    all_vpc_details = get_vpc_details_across_regions()
    
    if all_vpc_details:
        write_vpc_details_to_csv(all_vpc_details)
        print("VPC details have been written to 'vpc_details.csv'.")
    else:
        print("No VPC details found.")
