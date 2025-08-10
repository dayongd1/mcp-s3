#!/usr/bin/env python3
"""
Setup S3 bucket for MCP file upload server
"""
import boto3
import json
import uuid
from botocore.exceptions import ClientError

def create_bucket_name():
    """Generate a unique bucket name"""
    random_suffix = str(uuid.uuid4())[:8]
    return f"mcp-uploads-{random_suffix}"

def setup_s3_bucket():
    """Create and configure S3 bucket for MCP uploads"""
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # Generate unique bucket name
    bucket_name = create_bucket_name()
    
    try:
        print(f"🪣 Creating S3 bucket: {bucket_name}")
        
        # Get current region
        region = s3_client.meta.region_name or 'us-east-1'
        print(f"📍 Using region: {region}")
        
        # Create bucket
        if region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        print("✅ Bucket created successfully!")
        
        # Configure bucket settings
        configure_bucket_settings(s3_client, bucket_name)
        
        # Test bucket access
        test_bucket_access(s3_client, bucket_name)
        
        print(f"\n🎉 Setup complete!")
        print(f"📋 Bucket name: {bucket_name}")
        print(f"🔧 Use this command to start your MCP server:")
        print(f"   python mcp_box.py --bucket {bucket_name} --root /path/to/your/upload/folder")
        
        return bucket_name
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            print(f"❌ Bucket name {bucket_name} already exists globally. Trying another...")
            return setup_s3_bucket()  # Retry with new name
        else:
            print(f"❌ Error creating bucket: {e}")
            return None

def configure_bucket_settings(s3_client, bucket_name):
    """Configure bucket with security and lifecycle settings"""
    
    print("🔒 Configuring bucket security...")
    
    try:
        # Block public access (security best practice)
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print("  ✅ Public access blocked")
        
        # Enable versioning (optional but recommended)
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("  ✅ Versioning enabled")
        
        # Set up lifecycle policy to clean up old uploads
        lifecycle_policy = {
            'Rules': [
                {
                    'ID': 'DeleteOldUploads',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': ''},
                    'Expiration': {'Days': 30},  # Delete files after 30 days
                    'NoncurrentVersionExpiration': {'NoncurrentDays': 7}
                }
            ]
        }
        
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_policy
        )
        print("  ✅ Lifecycle policy set (30-day retention)")
        
        # Enable server-side encryption
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }
                ]
            }
        )
        print("  ✅ Server-side encryption enabled")
        
    except ClientError as e:
        print(f"  ⚠️ Warning: Could not configure some settings: {e}")

def test_bucket_access(s3_client, bucket_name):
    """Test bucket read/write access"""
    
    print("🧪 Testing bucket access...")
    
    try:
        # Test write access
        test_key = "test-access.txt"
        test_content = "MCP server access test"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8')
        )
        print("  ✅ Write access confirmed")
        
        # Test read access
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        content = response['Body'].read().decode('utf-8')
        assert content == test_content
        print("  ✅ Read access confirmed")
        
        # Test presigned URL generation
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print("  ✅ Presigned URL generation confirmed")
        
        # Clean up test object
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print("  ✅ Test cleanup completed")
        
    except Exception as e:
        print(f"  ❌ Access test failed: {e}")

def check_aws_credentials():
    """Verify AWS credentials are configured"""
    
    print("🔐 Checking AWS credentials...")
    
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        
        print(f"  ✅ AWS Account ID: {identity['Account']}")
        print(f"  ✅ User/Role ARN: {identity['Arn']}")
        return True
        
    except Exception as e:
        print(f"  ❌ AWS credentials not configured: {e}")
        print("\n🛠️ Please configure AWS credentials first:")
        print("   Option 1: aws configure")
        print("   Option 2: Set environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False

if __name__ == "__main__":
    print("🚀 Setting up S3 bucket for MCP file upload server...\n")
    
    if not check_aws_credentials():
        exit(1)
    
    bucket_name = setup_s3_bucket()
    
    if bucket_name:
        print(f"\n📝 Save this bucket name: {bucket_name}")
        print("🔄 You can now test your MCP server!")
    else:
        print("\n❌ Setup failed. Please check your AWS permissions.") 