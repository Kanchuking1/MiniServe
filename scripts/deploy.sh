# Make the MiniServe directory on the EC2 instance
ssh -i OMEN.pem ec2-user@ec2-3-22-242-31.us-east-2.compute.amazonaws.com "mkdir -p ~/MiniServe"

# Copy the files to the EC2 instance
scp -i OMEN.pem -r . ec2-user@ec2-3-22-242-31.us-east-2.compute.amazonaws.com:~/MiniServe/