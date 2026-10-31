import base64
import hashlib
import json
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
import config

# Desktop OAuth 2.0 sign-in using the authorization code flow:
# 1. Open the provider's sign-in page in the browser
# 2. Wait for the provider to redirect back to a small local server (http://localhost:8765/callback)
# 3. Exchange the code for an access token and read the user's profile

USER_AGENT = f"{config.app_name} (CustomTkinter desktop app)"

# Only one sign-in can wait on the local port at a time
_sign_in_lock = threading.Lock()

class OAuthError(Exception):
    # Raised with a message that can be shown to the user
    pass

def parse_google_profile(data):
    # Convert a Google profile into the app's profile format
    return {
        "id": data.get("sub"),
        "email": data.get("email"),
        "email_verified": bool(data.get("email_verified")),
        "first_name": data.get("given_name") or data.get("name", ""),
        "last_name": data.get("family_name", ""),
        "username": (data.get("email") or "").split("@")[0],
    }

def parse_facebook_profile(data):
    # Convert a Facebook profile into the app's profile format (Facebook only returns confirmed emails)
    return {
        "id": data.get("id"),
        "email": data.get("email"),
        "email_verified": bool(data.get("email")),
        "first_name": data.get("first_name") or data.get("name", ""),
        "last_name": data.get("last_name", ""),
        "username": (data.get("email") or data.get("name") or "").split("@")[0],
    }

def parse_discord_profile(data):
    # Convert a Discord profile into the app's profile format
    display_name = data.get("global_name") or data.get("username", "")
    return {
        "id": data.get("id"),
        "email": data.get("email"),
        "email_verified": bool(data.get("verified")),
        "first_name": display_name,
        "last_name": "",
        "username": data.get("username", ""),
    }

# Provider endpoints and settings
OAUTH_PROVIDERS = {
    "google": {
        "name": "Google",
        "client_id": config.google_client_id,
        "client_secret": config.google_client_secret,
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "token_method": "POST",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid email profile",
        "extra_auth_params": {"prompt": "select_account"},
        "use_pkce": True,
        "parse_profile": parse_google_profile,
    },
    "facebook": {
        "name": "Facebook",
        "client_id": config.facebook_client_id,
        "client_secret": config.facebook_client_secret,
        "auth_url": f"https://www.facebook.com/{config.facebook_api_version}/dialog/oauth",
        "token_url": f"https://graph.facebook.com/{config.facebook_api_version}/oauth/access_token",
        "token_method": "GET",
        "userinfo_url": f"https://graph.facebook.com/{config.facebook_api_version}/me?fields=id,name,first_name,last_name,email",
        "scope": "email public_profile",
        "extra_auth_params": {},
        "use_pkce": False,
        "parse_profile": parse_facebook_profile,
    },
    "discord": {
        "name": "Discord",
        "client_id": config.discord_client_id,
        "client_secret": config.discord_client_secret,
        "auth_url": "https://discord.com/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "token_method": "POST",
        "userinfo_url": "https://discord.com/api/users/@me",
        "scope": "identify email",
        "extra_auth_params": {"prompt": "consent"},
        "use_pkce": False,
        "parse_profile": parse_discord_profile,
    },
}

def get_redirect_uri():
    # The exact redirect URI to register in each provider's developer console
    return f"http://{config.oauth_redirect_host}:{config.oauth_redirect_port}{config.oauth_redirect_path}"

def get_provider_name(provider):
    # Display name of a provider, e.g. "google" -> "Google"
    return OAUTH_PROVIDERS.get(provider, {}).get("name", provider.title())

def get_display_providers():
    # Providers from config.oauth_providers that this app supports, in the configured order
    return [provider for provider in config.oauth_providers if provider in OAUTH_PROVIDERS]

def is_provider_configured(provider):
    # A provider is ready when it has a client id and secret
    settings = OAUTH_PROVIDERS.get(provider)
    return bool(settings and settings["client_id"] and settings["client_secret"])

def generate_pkce_pair():
    # Create a PKCE code verifier and its SHA-256 challenge
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge

def build_authorization_url(provider, state, code_challenge=None):
    # Build the URL of the provider's sign-in page
    settings = OAUTH_PROVIDERS[provider]
    params = {
        "client_id": settings["client_id"],
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": settings["scope"],
        "state": state,
        **settings["extra_auth_params"],
    }
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    return f"{settings['auth_url']}?{urlencode(params)}"

def wait_for_callback(expected_state, timeout=None):
    # Start a local server and wait for the provider to redirect back with a code
    timeout = timeout or config.oauth_timeout
    result = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            if url.path != config.oauth_redirect_path:
                self.send_response(404)
                self.end_headers()
                return
            query = parse_qs(url.query)
            result["code"] = query.get("code", [None])[0]
            result["state"] = query.get("state", [None])[0]
            result["error"] = query.get("error_description", query.get("error", [None]))[0]

            # Show a small page so the user knows they can go back to the app
            success = result["code"] and not result["error"]
            message = "You are signed in. You can close this tab and return to the app." if success else "Sign-in was cancelled or failed. You can close this tab."
            page = f"<html><body style='font-family:sans-serif;text-align:center;padding-top:80px'><h2>{config.app_name}</h2><p>{message}</p></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode())

        def log_message(self, format, *args):
            # Keep the console clean
            pass

    try:
        server = HTTPServer(("127.0.0.1", config.oauth_redirect_port), CallbackHandler)
    except OSError:
        raise OAuthError(f"Port {config.oauth_redirect_port} is in use. Change OAUTH_REDIRECT_PORT in .env.")

    deadline = time.monotonic() + timeout
    try:
        # Ignore unrelated requests (like /favicon.ico) until the callback arrives or time runs out
        while "code" not in result:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            server.timeout = remaining
            server.handle_request()
    finally:
        server.server_close()

    if not result:
        raise OAuthError("Sign-in timed out. Please try again.")
    if result.get("error") or not result.get("code"):
        raise OAuthError(f"Sign-in failed: {result.get('error') or 'no code received'}.")
    # The state must match to protect against forged callbacks (CSRF)
    if not result.get("state") or not secrets.compare_digest(result["state"], expected_state):
        raise OAuthError("Sign-in failed: invalid state. Please try again.")
    return result["code"]

def http_json(url, data=None, headers=None, method="GET"):
    # Send a request and return the JSON response
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT, **(headers or {})}
    body = None
    if data is not None:
        if method == "GET":
            url = f"{url}{'&' if '?' in url else '?'}{urlencode(data)}"
        else:
            body = urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        with urlopen(Request(url, data=body, headers=headers, method=method), timeout=20) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        details = e.read().decode(errors="ignore")[:200]
        raise OAuthError(f"Provider returned an error ({e.code}): {details}")
    except (URLError, TimeoutError, json.JSONDecodeError) as e:
        raise OAuthError(f"Could not reach the provider: {e}")

def exchange_code_for_token(provider, code, code_verifier=None):
    # Trade the authorization code for an access token
    settings = OAUTH_PROVIDERS[provider]
    data = {
        "client_id": settings["client_id"],
        "client_secret": settings["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": get_redirect_uri(),
    }
    if code_verifier:
        data["code_verifier"] = code_verifier
    token = http_json(settings["token_url"], data=data, method=settings["token_method"])
    if "access_token" not in token:
        raise OAuthError("Sign-in failed: no access token received.")
    return token["access_token"]

def fetch_user_profile(provider, access_token):
    # Read the signed in user's profile and convert it to the app's format
    settings = OAUTH_PROVIDERS[provider]
    data = http_json(settings["userinfo_url"], headers={"Authorization": f"Bearer {access_token}"})
    profile = settings["parse_profile"](data)
    if not profile.get("id"):
        raise OAuthError("Sign-in failed: the provider did not return a user id.")
    profile["provider"] = provider
    return profile

def oauth_sign_in(provider):
    # Run the full browser sign-in and return the user's profile (blocking, run it in a thread)
    if provider not in OAUTH_PROVIDERS:
        raise OAuthError(f"Unknown sign-in provider: {provider}")
    if not is_provider_configured(provider):
        name = get_provider_name(provider)
        raise OAuthError(f"{name} sign-in is not set up yet. Add {provider.upper()}_CLIENT_ID and "
                         f"{provider.upper()}_CLIENT_SECRET to your .env file.")
    if not _sign_in_lock.acquire(blocking=False):
        raise OAuthError("Another sign-in is already waiting in your browser.")

    try:
        state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = generate_pkce_pair() if OAUTH_PROVIDERS[provider]["use_pkce"] else (None, None)
        webbrowser.open(build_authorization_url(provider, state, code_challenge))
        code = wait_for_callback(state)
        access_token = exchange_code_for_token(provider, code, code_verifier)
        return fetch_user_profile(provider, access_token)
    finally:
        _sign_in_lock.release()
