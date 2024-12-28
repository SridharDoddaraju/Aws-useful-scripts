EC2 Volume Tagging Script
This script allows you to add tags to volumes attached to specified EC2 instances. It takes EC2 instance IDs as input, validates them, and then adds the following tags to any attached volumes:

Device_Name: The device name of the volume.
Project_xyz: A custom project tag (set to Yes).
Prerequisites
AWS CLI configured with appropriate IAM permissions to describe instances and create tags.
Bash shell environment.
How to Use
Save the script to a file, for example ec2_volume_tag.sh.
Make the script executable:
bash
Copy code
chmod +x ec2_volume_tag.sh
Run the script:
bash
Copy code
./ec2_volume_tag.sh
Enter the EC2 instance IDs when prompted. Use a comma-separated list of EC2 instance IDs (e.g., i-1234567890abcdef,i-abcdef1234567890).
The script will process each valid EC2 instance, check attached volumes, and add the appropriate tags.
Log File
The script generates a log file with the name ec2_volume_tag_log_YYYY-MM-DD_HH-MM-SS.log, where YYYY-MM-DD_HH-MM-SS is the timestamp when the script is run. This log contains details about the script execution, including:

Instance IDs processed.
Volumes and tags added.
Any warnings or errors encountered.
Example Output
vbnet
Copy code
Enter the EC2 instance IDs (comma-separated, e.g., i-1234567890abcdef,i-abcdef1234567890): i-0abcd1234efgh5678
Processing instance: i-0abcd1234efgh5678
Adding tags to volume vol-0abcd1234efgh5678 with device name /dev/sda1
Device_Name tag added successfully to volume vol-0abcd1234efgh5678
Project_CSI tag added successfully to volume vol-0abcd1234efgh5678
...
Script execution completed. Check ec2_volume_tag_log_2024-12-28_15-30-00.log for details.
Notes
The script will validate the provided EC2 instance IDs. If any are invalid, they will be skipped, and a warning will be logged.
If no valid EC2 instance IDs are provided, the script will exit with an error message.
License
This script is provided as-is. Use at your own risk.