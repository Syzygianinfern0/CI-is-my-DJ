import json
from argparse import ArgumentParser
from collections import OrderedDict

import gspread
import spotipy
from spotipy.oauth2 import SpotifyOAuth

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
    parser.add_argument("-d", help="Dry run", action="store_true")

    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    # Read Database
    gc = gspread.service_account(filename=args.c)
    worksheet = gc.open("CI Is My DJ").sheet1
    db_tracks = worksheet.get_values()
    db_tracks = OrderedDict({url: [title, [each for each in origin if len(each)]] for url, title, *origin in db_tracks})
    num_existing = len(db_tracks)
    print(f"Found {num_existing} entries in DB")

    # Aggregate all songs
    creds = json.load(open("credentials.json"))
    id, secret = creds["spotify_client_id"], creds["spotify_client_secret"]
    scope = "playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(id, secret, "http://example.com", scope=scope))

    updated_idx = []
    new_idx = []
    for playlist in SOURCES.values():
        playlist_name = sp.playlist(playlist)["name"]
        tracks = get_all_tracks(sp, playlist)
        for track in tracks:
            url = track["track"]["external_urls"]["spotify"]
            if url in db_tracks.keys():
                if playlist_name not in db_tracks[url][1]:
                    db_tracks[url][1].append(playlist_name)
                    updated_idx.append(list(db_tracks.keys()).index(url))
            else:
                db_tracks[url] = [track["track"]["name"], [playlist_name]]
                new_idx.append(list(db_tracks.keys()).index(url))

    if not args.d:
        # Update Playlist
        if len(new_idx):
            urls = [each[0] for each in list(db_tracks.items())[new_idx[0] :]]
            [sp.playlist_add_items(TARGET, urls[idx : idx + 100]) for idx in range(0, len(urls), 100)]

            # TODO: Implement auto monthly digests
            dec_id = "2emmetze5gmxnAhF2mt0x6"
            [sp.playlist_add_items(dec_id, urls[idx : idx + 100]) for idx in range(0, len(urls), 100)]

        # Update DB
        if len(new_idx):
            worksheet.update(
                f"A{new_idx[0] + 1}",
                [
                    [each[0], each[1], *each[2]]
                    for each in [[key, *value] for key, value in list(db_tracks.items())[new_idx[0] :]]
                ],
            )
        updated_idx = list(set(updated_idx) - set(new_idx))
        for idx in updated_idx:
            worksheet.update(
                f"A{idx + 1}",
                [
                    [each[0], each[1], *each[2]]
                    for each in [[key, *value] for key, value in [list(db_tracks.items())[idx]]]
                ],
            )
        print(f"Updated database and playlists with {len(new_idx)} new tracks and {len(updated_idx)} updates")


if __name__ == "__main__":
    main()
