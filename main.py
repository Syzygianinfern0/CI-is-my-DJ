import itertools
import json
from argparse import ArgumentParser

import gspread
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SOURCES = {
    "Today's Top Hits": "37i9dQZF1DXcBWIGoYBM5M",
    "Teen Beats": "37i9dQZF1DWWvvyNmW9V9a",
}


def sheets_get_values(worksheet):
    return worksheet.get_values()


def sheets_set_values(worksheet, values):
    return worksheet.update("A1", values)


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
    values = sheets_get_values(worksheet)
    print(f"Found {len(values)} entries in DB")

    # Aggregate all songs
    creds = json.load(open("credentials.json"))
    id, secret = creds["spotify_client_id"], creds["spotify_client_secret"]
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(id, secret))
    tracks = [get_all_tracks(sp, playlist) for playlist in SOURCES.values()]
    tracks = itertools.chain.from_iterable(tracks)
    tracks = [[each["track"]["external_urls"]["spotify"], each["track"]["name"]] for each in tracks]
    tracks = list(set([tuple(track) for track in tracks]))  # remove duplicates
    print(f"Found {len(tracks)} tracks in total")

    # Find new songs

    # Update Playlist

    # Update DB


if __name__ == "__main__":
    main()
