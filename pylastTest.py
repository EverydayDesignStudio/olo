#-*-coding:utf-8-*-

import pylast, pprint

API_KEY = 'e38cc7822bd7476fe4083e36ee69748e'
USER_NAME = 'username'

network = pylast.LastFMNetwork(api_key=API_KEY, username=USER_NAME)

user = network.get_user(USER_NAME)
tracks = user.get_recent_tracks(limit = None)
for track in tracks:
    # maybe we don't need to encode to utf, save it straight to the local database
    print([track.timestamp, track[0].artist.name.encode('utf-8'), track[0].title.encode('utf-8'), track.album])

print("@@@ " + str(len(tracks)) + " tracks in total.")
