
from supabase import create_client
import os

SUPABASE_URL = "https://juhkarrjmlwjwjtbysnn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp1aGthcnJqbWx3andqdGJ5c25uIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTk3MDU5OCwiZXhwIjoyMDk1NTQ2NTk4fQ.xpcHuc1Qojq308mOaiGEj6nM8CwviTvN2OMVO5hYAzM"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_image(file, filename):
    response = supabase.storage.from_("product-images").upload(
        filename,
        file
    )

    public_url = supabase.storage.from_("product-images").get_public_url(filename)
    return public_url