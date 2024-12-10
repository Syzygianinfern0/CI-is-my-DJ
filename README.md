![Logo](assets/ci-is-my-dj.png)

# CI is my DJ

> Cuz why not lmao

## Why?

Because I am too lazy to find new songs. I want to automate the process of finding new songs and adding them to a playlist.

## How?

I love Spotify's curated playlists (Today's Top Hits, Teen Beats, etc.). So I created a script which scans for new songs in those and adds them to a monthly updating digest! This is run as a GitHub Action every day right here.

<p align="center">
    <a href="https://docs.google.com/spreadsheets/d/18B2xp9Oi4o4ZBESBdRpoedA4T9CItZDkxEYxy_s-wBc/edit?usp=sharing">Google Sheets as the database</a>
</p>

<p align="center">
    <a href="https://open.spotify.com/user/djnkqfurl9v8ewx0mxpr68znh?si=ptZitSAETluyE3TtGrj59w">Playlists are public on my Spotify Profile</a>
</p>

## TODO

- [x] Implement basic functions
- [x] Make the fucking CI (urgent)
- [x] Automatic monthly playlist creation

## Usage

Get a credentials.json by (1) enable google drive api, (2) create service account, (3) json key for serivce account
