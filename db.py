import os
from supabase import create_client, Client

# Use environment variables for security! 
# You can use a .env file for these.
SUPABASE_URL = "https://givnpzimnxbhqkgdoxic.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpdm5wemltbnhiaHFrZ2RveGljIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTYzODIzMCwiZXhwIjoyMDk3MjE0MjMwfQ.sTb5cApsApjenNjoE5kqKLMBsi1OxPxrI1sC9dOvQR4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)