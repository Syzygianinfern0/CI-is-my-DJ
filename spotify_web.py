"""
Fetches Spotify playlist data via the internal web player partner API.

This bypasses the public Spotify API's restrictions on curated editorial
playlists (37i9dQZF1D...) by replicating the token acquisition and GraphQL
requests the Spotify web player makes in the browser.
"""

import hashlib
import hmac
import time

import requests

_APP_VERSION = "1.2.88.305.ge4c8ab84"
_PERSISTED_QUERY_HASH = "32b05e92e438438408674f95d0fdad8082865dc32acd55bd97f5113b8579092b"
_TOTP_SECRETS_URL = "https://git.gay/thereallo/totp-secrets/raw/branch/main/secrets/secretDict.json"
_BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"


def _get_secret(inp):
    secret = [str(item ^ ((index % 33) + 9)) for index, item in enumerate(inp)]
    return [ord(c) for c in "".join(secret)]


def _counter_to_bytes(counter):
    result = bytearray(8)
    for i in range(7, -1, -1):
        result[i] = counter & 0xFF
        counter >>= 8
    return bytes(result)


def _generate_totp(session):
    secrets = session.get(_TOTP_SECRETS_URL, timeout=10).json()
    version = max(secrets, key=int)
    key = bytearray(_get_secret(secrets[version]))
    data = _counter_to_bytes(int(time.time()) // 30)
    h = hmac.new(key, data, hashlib.sha1).digest()
    offset = h[-1] & 0xF
    binary = (
        (h[offset] & 0x7F) << 24 | (h[offset + 1] & 0xFF) << 16 | (h[offset + 2] & 0xFF) << 8 | (h[offset + 3] & 0xFF)
    )
    return str(binary % 1_000_000).zfill(6)


class SpotifyWeb:
    """Thin client for reading Spotify playlists via the web player partner API."""

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "referer": "https://open.spotify.com/",
                "user-agent": _BROWSER_UA,
                "accept-language": "en",
            }
        )
        self._access_token = None
        self._client_token = None
        self._token_expiry = 0

    def _ensure_tokens(self):
        if time.time() < self._token_expiry - 60:
            return

        totp = _generate_totp(self._session)
        resp = self._session.get(
            "https://open.spotify.com/api/token",
            params={"productType": "web-player", "totp": totp, "totpVer": 5},
            timeout=10,
        )
        resp.raise_for_status()
        token_data = resp.json()
        self._access_token = token_data["accessToken"]
        self._token_expiry = token_data["accessTokenExpirationTimestampMs"] / 1000
        client_id = token_data["clientId"]

        resp = self._session.post(
            "https://clienttoken.spotify.com/v1/clienttoken",
            headers={"accept": "application/json", "content-type": "application/json"},
            json={
                "client_data": {
                    "client_version": _APP_VERSION,
                    "client_id": client_id,
                    "js_sdk_data": {
                        "device_brand": "Apple",
                        "device_model": "unknown",
                        "os": "macos",
                        "os_version": "10.15.7",
                        "device_type": "computer",
                    },
                }
            },
            timeout=10,
        )
        resp.raise_for_status()
        self._client_token = resp.json()["granted_token"]["token"]

    def _query(self, operation, variables):
        self._ensure_tokens()
        resp = self._session.post(
            "https://api-partner.spotify.com/pathfinder/v2/query",
            headers={
                "authorization": f"Bearer {self._access_token}",
                "client-token": self._client_token,
                "app-platform": "WebPlayer",
                "spotify-app-version": _APP_VERSION,
                "content-type": "application/json;charset=UTF-8",
                "accept": "application/json",
            },
            json={
                "variables": variables,
                "operationName": operation,
                "extensions": {"persistedQuery": {"version": 1, "sha256Hash": _PERSISTED_QUERY_HASH}},
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_playlist_name(self, playlist_id):
        data = self._query(
            "fetchPlaylist",
            {
                "uri": f"spotify:playlist:{playlist_id}",
                "offset": 0,
                "limit": 1,
                "enableWatchFeedEntrypoint": False,
                "includeEpisodeContentRatingsV2": False,
            },
        )
        return data["data"]["playlistV2"]["name"]

    def get_all_tracks(self, playlist_id):
        """
        Returns a list of track dicts with the same shape as spotipy's
        playlist_items() response items:
            {"track": {"name": ..., "external_urls": {"spotify": ...}}}
        Returns None entries for non-track items (episodes etc.), matching
        the original spotipy behaviour that callers already handle.
        """
        tracks = []
        offset = 0
        limit = 50
        total = None

        while total is None or offset < total:
            operation = "fetchPlaylist" if offset == 0 else "fetchPlaylistContents"
            variables = {
                "uri": f"spotify:playlist:{playlist_id}",
                "offset": offset,
                "limit": limit,
                "includeEpisodeContentRatingsV2": False,
            }
            if offset == 0:
                variables["enableWatchFeedEntrypoint"] = False

            data = self._query(operation, variables)
            content = data["data"]["playlistV2"]["content"]

            if total is None:
                total = content["totalCount"]

            for item in content["items"]:
                item_data = item.get("itemV2", {}).get("data", {})
                if item_data.get("__typename") != "Track":
                    tracks.append(None)
                    continue
                uri = item_data.get("uri", "")
                track_id = uri.split(":")[-1]
                tracks.append(
                    {
                        "track": {
                            "name": item_data.get("name"),
                            "external_urls": {"spotify": f"https://open.spotify.com/track/{track_id}"},
                        }
                    }
                )

            offset += len(content["items"])

        return tracks
