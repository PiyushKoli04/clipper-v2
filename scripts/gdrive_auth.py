"""Helper script to obtain Google Drive OAuth2 refresh token for personal account.

Run locally once:
    python scripts/gdrive_auth.py

Follow browser instructions, grant Drive permissions, and paste the code back.
Copy the generated GDRIVE_REFRESH_TOKEN into your .env and GitHub Secrets.
"""

import sys
import urllib.parse
import httpx

SCOPES = ["https://www.googleapis.com/auth/drive"]
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost:8080"


def main():
    print("=" * 60)
    print("Clipper v2 - Google Drive OAuth Token Generator")
    print("=" * 60)
    client_id = input("Enter your GDRIVE_CLIENT_ID: ").strip()
    client_secret = input("Enter your GDRIVE_CLIENT_SECRET: ").strip()

    if not client_id or not client_secret:
        print("Client ID and Secret are required.")
        sys.exit(1)

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("\n1. Open this URL in your browser:")
    print(url)
    print("\n2. Log in and accept permissions.")
    print("3. You will be redirected to localhost (which may fail to load).")
    print("4. Copy the entire redirect URL from your browser address bar:")
    redirect_input = input("Paste redirected URL or authorization code here: ").strip()

    code = redirect_input
    if "code=" in redirect_input:
        query = urllib.parse.urlparse(redirect_input).query
        code = urllib.parse.parse_qs(query).get("code", [code])[0]

    print("\nExchanging code for refresh token...")
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )

    if resp.status_code != 200:
        print(f"Error ({resp.status_code}): {resp.text}")
        sys.exit(1)

    data = resp.json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        print("Warning: No refresh token in response (did you prompt=consent?). Response:")
        print(data)
    else:
        print("\nSUCCESS! Here is your refresh token:")
        print("-" * 60)
        print(f"GDRIVE_REFRESH_TOKEN={refresh_token}")
        print("-" * 60)
        print("Save this in your .env and GitHub Secrets!")


if __name__ == "__main__":
    main()
