import itertools
import json
from argparse import ArgumentParser

import gspread
import spotipy
from ordered_set import OrderedSet
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

SOURCES = {
    "Today's Top Hits": "37i9dQZF1DXcBWIGoYBM5M",
    "Sad Songs": "37i9dQZF1DX7qK8ma5wgG1",
    "Teen Beats": "37i9dQZF1DWWvvyNmW9V9a",
    "Night Pop": "37i9dQZF1DXbcP8BbYEQaO",
    "Sad Bops": "37i9dQZF1DWZUAeYvs88zc",
    "Mellow Pop": "37i9dQZF1DWYp3yzk1civi",
    "songs to scream in the car": "37i9dQZF1DX4mWCZw6qYIw",
    "Pop Party": "37i9dQZF1DWXti3N4Wp5xy",
    "Soft Pop Hits": "37i9dQZF1DWTwnEm1IYyoj",
    "Pop Sauce": "37i9dQZF1DXaPCIWxzZwR1",
    "Chill Pop": "37i9dQZF1DX0MLFaUdXnjA",
    "Love Pop": "37i9dQZF1DX50QitC6Oqtn",
}

TARGET = "53czPuORoRkVxKgQCBz4b6"


def get_all_tracks(sp, playlist):
    results = sp.playlist_items(playlist)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    return tracks


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-i", default="CI Is My DJ", help="Name of Sheet")
    parser.add_argument("-c", default="credentials.json", help="Path to credentials.json")
    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    # Read Database
    gc = gspread.service_account(filename=args.c)
    worksheet = gc.open("CI Is My DJ").sheet1
    db_tracks = worksheet.get_values()
    db_tracks = OrderedSet([tuple(track) for track in db_tracks])
    print(f"Found {len(db_tracks)} entries in DB")

    # Aggregate all songs
    creds = json.load(open("credentials.json"))
    id, secret = creds["spotify_client_id"], creds["spotify_client_secret"]
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(id, secret))
    tracks = [get_all_tracks(sp, playlist) for playlist in SOURCES.values()]
    tracks = itertools.chain.from_iterable(tracks)
    tracks = [[each["track"]["external_urls"]["spotify"], each["track"]["name"]] for each in tracks]
    tracks = OrderedSet([tuple(track) for track in tracks])  # remove duplicates
    print(f"Found {len(tracks)} tracks in total")

    # Find new songs
    new_tracks = tracks - db_tracks
    print(f"Found {len(new_tracks)} new tracks in total")

    # Update Playlist
    # TODO: Implement checking for DB and playlists
    scope = "playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(id, secret, "http://example.com", scope=scope))
    urls = [each[0] for each in new_tracks.items]
    [sp.playlist_add_items(TARGET, urls[idx : idx + 100]) for idx in range(0, len(urls), 100)]

    # TODO: Implement auto monthly digests
    dec_id = "2emmetze5gmxnAhF2mt0x6"
    [sp.playlist_add_items(dec_id, urls[idx : idx + 100]) for idx in range(0, len(urls), 100)]
    print(f"Updated target playlist with {len(new_tracks)} tracks")

    # Update DB
    worksheet.update(f"A{len(db_tracks) + 1}", new_tracks.items)
    print(f"Updated database with {len(new_tracks)} tracks")


if __name__ == "__main__":
    main()
