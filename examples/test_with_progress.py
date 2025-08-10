#!/usr/bin/env python3
"""
Test MCP server with progress tracking
"""
import asyncio
import tempfile
import os
from fastmcp import Client
from dotenv import load_dotenv

async def progress_handler(progress: float, total: float | None, message: str | None):
    """Handle progress updates from the server"""
    if total is not None:
        percentage = (progress / total) * 100
        bar_length = 40
        filled_length = int(bar_length * progress / total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\r📊 Progress: [{bar}] {percentage:.1f}% {message or ''}", end='', flush=True)
    else:
        print(f"\r📊 Progress: {progress} {message or ''}", end='', flush=True)

async def test_with_progress():
    """Test server with progress tracking"""
    
    # Load environment variables
    load_dotenv()
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    if not bucket_name:
        print("❌ S3_BUCKET_NAME not found in .env file")
        return
    
    # Create test upload directory
    upload_dir = os.path.expanduser("~/mcp-uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create a larger test file to see progress
    print("📝 Creating test file...")
    test_content = "This is test data for progress tracking.\n" * 50000  # ~1.7MB
    test_file_path = os.path.join(upload_dir, "large-test.txt")
    
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    file_size = os.path.getsize(test_file_path)
    print(f"📏 Created test file: {file_size:,} bytes")
    
    try:
        # Connect with progress handler
        from fastmcp.client.transports import StdioTransport
        from dotenv import dotenv_values
        
        # Pass environment variables to the server subprocess
        env_vars = dotenv_values('.env')
        
        transport = StdioTransport(
            command="python",
            args=["mcp_s3.py", "--root", upload_dir],
            env=env_vars
        )
        client = Client(transport, progress_handler=progress_handler)
        
        async with client:
            print("🚀 Starting upload with progress tracking...")
            
            result = await client.call_tool("upload_file", {
                "local_path": "large-test.txt",  # Relative to upload directory
                "expires_in": 3600
            })
            
            print(f"\n✅ Upload completed!")
            print(f"🔗 URL: {result.data.url[:50]}...")
            print(f"📏 Final size: {result.data.size:,} bytes")
            print(f"🪣 Uploaded to bucket: {bucket_name}")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print("🧹 Test file cleaned up")

if __name__ == "__main__":
    asyncio.run(test_with_progress()) 