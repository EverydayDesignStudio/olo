# https://developer.spotify.com/documentation/general/guides/scopes/
#-*-coding:utf-8-*-

import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
import pprint
import sh
sh.init()

# ### TODO: argument handling
# parser = argparse.ArgumentParser()
# parser.add_argument('--query',
#     action="store", dest="query",
#     help="query string", default="spam")
#
# options, args = parser.parse_args()
#
# print 'Query string:', options.query

scope = "user-modify-playback-state"
# scope = 'user-read-playback-state'

### Auth for the app
# username = '31r27sr4fzqqd24rbs65vntslaoq'
# client_id = '3f77a1d68f404a7cb5e63614fca549e3'
# client_secret = '966f425775d7403cbbd66b838b23a488'
# # device_oloradio1 = '1daca38d2ae160b6f1b8f4919655275043b2e5b4'
# device_desktop = '2358d9d7c020e03c0599e66bb3cb244347dfe392'

redirect_uri = "https://example.com/callback/"

# username = "9mgcb91qlhdu2kh4nwj83p165"
username = sh.spotify_username
client_id = "86456db5c5364110aa9372794e146bf9"
client_secret = "cd7177a48c3b4ea2a6139b88c1ca87f5"
# device_oloradio1 = "984b0223d4e3c3fec177a61e40c42c935217020c"
device_oloradio1 = sh.device_oloradio1
# this is for olo2
#device_oloradio1 = "98bb0735e28656bac098d927d410c3138a4b5bca"


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

# songTitle = "colors"
# artist = "stella jang"
# album = "colors"
#
# query_basic = '''"{}" artist:{}'''.format(songTitle, artist);
# query_with_album = '''"{}" artist:{} album:{}'''.format(songTitle, artist, album);

uri = "spotify:track:5lNuqFVMca4vPupY10cH0J"

# sp = spotipy.Spotify(auth=token)
# res = sp.devices()
# pprint.pprint(res)
# quit();

if token:
    sp = spotipy.Spotify(auth=token)
    # result = sp.search(q=query_with_album, type="track")
    # tracks = result['tracks'];
    # pprint.pprint(tracks)
    # # try again with out album name
    # if (tracks['total'] == 0):
    #     pprint.pprint("### Found no track, Retrying..")
    #     result = sp.search(q=query_basic, type="track")
    #     tracks = result['tracks'];
    #     pprint.pprint(tracks)
    # for item in tracks['items']:
    #     trackuri = item['uri']
    #     print(item['name'], item['uri']);
    #     break;

    print("@@ Pausing and Playing,,");
    sp.pause_playback(device_id = device_oloradio1)
    sp.start_playback(device_id = device_oloradio1, uris = [uri])

val = 0;
while (True):
    val = input("volume?: ")
    if (val == 'p'):
        print("@@@ pausing,,")
#        sp.pause_playback(device_id = device_oloradio1);
        sp.pause_playback(device_id=device_oloradio1);
    elif (val == 's'):
        print("@@@ starting,,")
#        sp.start_playback(device_id = device_oloradio1, uris = [uri])
        sp.start_playback(uris = [uri])
    elif (int(val) >= 0 and int(val) <= 100):
        sp.volume(int(val), device_id=device_oloradio1)
    else:
        break;

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
