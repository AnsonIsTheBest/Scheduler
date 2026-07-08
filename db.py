import os
from supabase import create_client, Client

# Use environment variables for security! 
# You can use a .env file for these.

supabase: Client = create_client(os.getenv(SUPABASE_URL),os.getenv(SUPABASE_KEY))