from supabase import create_client, Client

from app.database.config import (
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
)


# Backend database client.
# Used for trusted server-side database operations.
supabase_admin: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


# Authentication client.
# Used for sign-in operations.
supabase_auth: Client = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
)

# Backwards-compatible alias for existing backend routes.
supabase = supabase_admin