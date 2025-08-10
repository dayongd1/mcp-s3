#!/usr/bin/env python3
"""
Test AWS S3 connection using credentials from .env file
"""
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

def test_aws_credentials():
    """Test AWS credentials and S3 access"""
    
    print("🔐 Testing AWS credentials from .env file...\n")
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') 
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    # Validate required variables are present
    missing_vars = []
    if not access_key:
        missing_vars.append('AWS_ACCESS_KEY_ID')
    if not secret_key:
        missing_vars.append('AWS_SECRET_ACCESS_KEY')
    if not bucket_name:
        missing_vars.append('S3_BUCKET_NAME')
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Create a .env file with the following format:")
        print("AWS_ACCESS_KEY_ID=your_access_key_here")
        print("AWS_SECRET_ACCESS_KEY=your_secret_key_here") 
        print("AWS_DEFAULT_REGION=us-east-1")
        print("S3_BUCKET_NAME=your_bucket_name_here")
        return False
    
    try:
        # Test STS (Security Token Service) - validates credentials
        print("1️⃣ Testing AWS credentials...")
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        identity = sts_client.get_caller_identity()
        print(f"   ✅ Credentials valid!")
        print(f"   🆔 Account ID: {identity['Account']}")
        print(f"   👤 User ARN: {identity['Arn']}")
        
        # Test S3 client creation
        print("\n2️⃣ Testing S3 client...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        print(f"   ✅ S3 client created successfully!")
        print(f"   🌍 Region: {region}")
        
        # Test bucket access
        print(f"\n3️⃣ Testing access to bucket '{bucket_name}'...")
        
        # Check if bucket exists and is accessible
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"   ✅ Bucket '{bucket_name}' exists and is accessible!")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"   ❌ Bucket '{bucket_name}' does not exist!")
                return False
            elif error_code == '403':
                print(f"   ❌ Access denied to bucket '{bucket_name}'!")
                print("   💡 Check your IAM user permissions")
                return False
            else:
                print(f"   ❌ Error accessing bucket: {e}")
                return False
        
        # Test upload permission
        print("\n4️⃣ Testing upload permission...")
        test_key = "test-connection.txt"
        test_content = "MCP server connection test"
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content.encode('utf-8')
            )
            print("   ✅ Upload permission confirmed!")
        except ClientError as e:
            print(f"   ❌ Upload failed: {e}")
            return False
        
        # Test download permission
        print("\n5️⃣ Testing download permission...")
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
            content = response['Body'].read().decode('utf-8')
            if content == test_content:
                print("   ✅ Download permission confirmed!")
            else:
                print("   ❌ Downloaded content doesn't match!")
                return False
        except ClientError as e:
            print(f"   ❌ Download failed: {e}")
            return False
        
        # Test presigned URL generation
        print("\n6️⃣ Testing presigned URL generation...")
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': test_key},
                ExpiresIn=3600
            )
            print("   ✅ Presigned URL generated successfully!")
            print(f"   🔗 URL: {presigned_url[:60]}...")
        except Exception as e:
            print(f"   ❌ Presigned URL generation failed: {e}")
            return False
        
        # Clean up test file
        print("\n7️⃣ Cleaning up test file...")
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            print("   ✅ Test file deleted!")
        except ClientError as e:
            print(f"   ⚠️ Warning: Could not delete test file: {e}")
        
        print(f"\n🎉 All tests passed! Your AWS setup is working correctly.")
        print(f"🚀 You can now run your MCP server with:")
        print(f"   python mcp_box.py --bucket {bucket_name} --root /path/to/upload/folder")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid!")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidAccessKeyId':
            print("❌ Invalid AWS Access Key ID!")
        elif error_code == 'SignatureDoesNotMatch':
            print("❌ Invalid AWS Secret Access Key!")
        else:
            print(f"❌ AWS Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 AWS S3 Connection Test\n")
    print("📋 This script will test your AWS credentials from .env file\n")
    
    if test_aws_credentials():
        print("\n✅ Setup is ready for MCP server!")
    else:
        print("\n❌ Please fix the issues above before running the MCP server.")
        print("\n💡 Need help?")
        print("   1. Check your .env file has the correct credentials")
        print("   2. Verify your IAM user has S3 permissions") 
        print("   3. Confirm your bucket name is correct") 