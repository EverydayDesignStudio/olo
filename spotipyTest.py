# https://developer.spotify.com/documentation/general/guides/scopes/
#-*-coding:utf-8-*-

import urllib
import json

import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
import pprint
import argparse

# ### TODO: argument handling
# parser = argparse.ArgumentParser()
# parser.add_argument('--query',
#     action="store", dest="query",
#     help="query string", default="spam")
#
# options, args = parser.parse_args()
#
# print 'Query string:', options.query

scope = 'user-modify-playback-state'

### Auth for the app
username = '31r27sr4fzqqd24rbs65vntslaoq'
client_id = '3f77a1d68f404a7cb5e63614fca549e3'
client_secret = '966f425775d7403cbbd66b838b23a488'
# device_oloradio1 = '1daca38d2ae160b6f1b8f4919655275043b2e5b4'
device_desktop = '2358d9d7c020e03c0599e66bb3cb244347dfe392'

redirect_uri = 'https://example.com/callback/'

# username = '9mgcb91qlhdu2kh4nwj83p165'
# client_id = '86456db5c5364110aa9372794e146bf9'
# client_secret = 'cd7177a48c3b4ea2a6139b88c1ca87f5'
# device_oloradio1 = 'edstudio2018'


token = util.prompt_for_user_token(username, scope, client_id = client_id, client_secret = client_secret, redirect_uri = redirect_uri)
# print(token);

### maybe getting the device name is just a one-time thing, or ignore it to automatically connect to the active device
# spotify = spotipy.Spotify(auth=token)
# response = spotify.devices();
# pprint.pprint(response)

### TODO: what to do if an auth token expires?
# sp_oauth = oauth2.SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri=redirect_uri,scope=scopes)
# token_info = sp_oauth.get_cached_token()
# if sp_oauth.is_token_expired(token_info):
#     token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
#     token = token_info['access_token']
#     sp = spotipy.Spotify(auth=token)

# if token:
#     sp = spotipy.Spotify(auth=token)
#     results = sp.pause_playback(device_id = '2358d9d7c020e03c0599e66bb3cb244347dfe392')
#     print(results)

songTitle = "colors"
artist = "stella jang"
album = "colors"

query_basic = '''"{}" artist:{}'''.format(songTitle, artist);
query_with_album = '''"{}" artist:{} album:{}'''.format(songTitle, artist, album);

u = 'spotify:track:7nGFwNl0OJVlDFvFW2VXNr'

sp = spotipy.Spotify(auth=token)
res = sp.current_playback()
pprint.pprint(res)
quit();

if token:
    sp = spotipy.Spotify(auth=token)
    result = sp.search(q=query_with_album, type="track")
    tracks = result['tracks'];
    pprint.pprint(tracks)
    # try again with out album name
    if (tracks['total'] == 0):
        pprint.pprint("### Found no track, Retrying..")
        result = sp.search(q=query_basic, type="track")
        tracks = result['tracks'];
        pprint.pprint(tracks)
    for item in tracks['items']:
        trackuri = item['uri']
        print(item['name'], item['uri']);
        break;

    sp.start_playback(device_id = device_desktop, uris = [trackuri])

### TODO: detect when the track has ended
# after 'duration_ms': n, check the track has ended
# sp.current_user_playing_track() == null, then ,,,

# if token:
#     sp = spotipy.Spotify(auth=token)
#     playlists = sp.user_playlists(username)
#     for playlist in playlists['items']:
#         print(playlist['name'])

# for track in response['tracks']:
#     print(track['name'])

# spotify.start_playback();
