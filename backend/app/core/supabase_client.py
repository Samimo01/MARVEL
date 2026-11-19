"""Client Supabase pour le Storage."""

from supabase import Client, create_client
from app.config import settings

supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
)

CAMPAIGNS_BUCKET = "campaigns"
NATURAL_DONATIONS_BUCKET = "natural_donations"