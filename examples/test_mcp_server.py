#!/usr/bin/env python3
"""
Test script for the MCP S3 upload server
"""
import asyncio
import tempfile
import os
from fastmcp import Client
from dotenv import load_dotenv

async def test_server():
    """Test the MCP server functionality"""
    
    # Load environment variables
    load_dotenv()
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    if not bucket_name:
        print("❌ S3_BUCKET_NAME not found in .env file")
        return
    
    # Create test upload directory
    upload_dir = os.path.expanduser("~/mcp-uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create a test file in the upload directory
    test_content = "Hello, this is a test file for MCP S3 upload!\n" * 100
    test_file_path = os.path.join(upload_dir, "test-upload.txt")
    
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    print(f"📝 Created test file: {test_file_path}")
    
    try:
        # Connect to the server
        print("🔌 Connecting to MCP server...")
        
        # Connect to the server script - FastMCP will handle launching it
        from fastmcp.client.transports import StdioTransport
        from dotenv import dotenv_values
        
        # Pass environment variables to the server subprocess
        env_vars = dotenv_values('.env')
        
        transport = StdioTransport(
            command="python",
            args=["mcp_s3.py", "--root", upload_dir],
            env=env_vars
        )
        client = Client(transport)
        
        async with client:
            # List available tools
            print("📋 Available tools:")
            tools = await client.list_tools()
            for tool in tools:
                print(f"  • {tool.name}: {tool.description}")
            
            print("\n📤 Testing file upload...")
            
            # Test the upload_file tool
            result = await client.call_tool("upload_file", {
                "local_path": "test-upload.txt",  # Relative to upload directory
                "expires_in": 3600  # 1 hour
            })
            
            print("✅ Upload successful!")
            print(f"📊 Result: {result.data}")
            print(f"🔗 Presigned URL: {result.data.url[:60]}...")
            print(f"📏 File size: {result.data.size:,} bytes")
            print(f"🎭 MIME type: {result.data.mime_type}")
            print(f"🔑 S3 key: {result.data.s3_key}")
            print(f"🪣 S3 bucket: {bucket_name}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print("🧹 Cleaned up test file")

if __name__ == "__main__":
    print("🚀 Starting MCP S3 upload server test...")
    asyncio.run(test_server()) 