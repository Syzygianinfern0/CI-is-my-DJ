import itertools
import json

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SOURCES = {
    "Today's Top Hits": "37i9dQZF1DXcBWIGoYBM5M",
    "Teen Beats": "37i9dQZF1DWWvvyNmW9V9a",
}


def get_all_tracks(sp, playlist):
    results = sp.playlist_items(playlist)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    return tracks


def main():
    creds = json.load(open("credentials.json"))
    id, secret = creds["spotify_client_id"], creds["spotify_client_secret"]

    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(id, secret),
    )

    tracks = [get_all_tracks(sp, playlist) for playlist in SOURCES.values()]
    tracks = itertools.chain.from_iterable(tracks)
    tracks = [[each["track"]["external_urls"]["spotify"], each["track"]["name"]] for each in tracks]
    print(len(tracks))

    tracks = list(set([tuple(track) for track in tracks]))  # remove duplicates
    print(len(tracks))


if __name__ == "__main__":
    main()
