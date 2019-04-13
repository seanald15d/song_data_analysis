import re
import time
import numpy as np

import discogs_client as dc

import lyricwikia as lw
from lyricwikia import LyricsNotFound

from Levenshtein import distance


def get_meta(a, t, y):

	r = re.compile('')
	d = dc.Client('APP_NAME', user_token='USER_TOKEN')

	# Search discogs client by author and title strings
	results = d.search(a + ' ' + t, type='release')
	
	l_r = results.pages
	
	if l_r == 1:
		results = [results[0]]
	else:
		results = [results[i] for i in range(0, l_r + 1)]
	
	year = [results[j] for j in range(0, len(results))]
	
	# try to get the single "album" right away if it exists
	hope = [j for j in year if t in str(j)]
	
	if len(hope) >= 1:
		# use string distance metric to find year closest to the current year in the current iteration
		y_dist = [distance(str(hope[j].year), str(y)) for j in range(0, len(hope))]
		ind = min(y_dist)
		indic = y_dist.index(ind)		
		year = [hope[indic]]
	else:
		y_dist = [distance(str(year[j].year), str(y)) for j in range(0, len(year))]
		ind = min(y_dist)
		indic = y_dist.index(ind)		
		year = [year[indic]]
	if len(year) >= 1:
		year_date = year[0].year

		# we want to take the first album in our list of "close" years
		# from discogs, most albums are formatted with artist - ablum name
		almost = str(year[0]).split(' - ')[1]

		# do some string manipulation to get the exact string we want
		if '"' in almost:
			album_name = almost.split('"')[0]
		elif "'" in almost:
			album_name = almost.split("'")[0]
		else:
			album_name = almost
		form = year[0].formats
		# help discern whether release is an album or single
		try:
			desc = form[0]['descriptions']

			if len(desc) > 1:
				if 'Album' in desc:
					album_single = 'Album'
				else:
					album_single = 'Single'
			else:
				album_single = desc[0]
		except KeyError:
			album_single = form[0]
		# get track list of release to discern if title given is even in the release
		# we found
		track_list = year[0].tracklist
		track_pos = [str(year[0].tracklist[i]).encode('utf-8').decode('utf-8') for i in range(0, len(year[0].tracklist))]
		r = re.compile(t)

		r2 = re.compile(r"Track '\d+'|Track 'CD-\d+'|Track '[A-Z]\d*'|Track '[A-Z]\d*'")
		# if we have more than one song, add all songs to list
		if len(track_pos) > 1:
			title_string = []

			for i in range(0, len(track_pos)):
				if '"' in str(track_pos[i]):
					title_string.append(track_pos[i].split('"')[1])
				else:
					title_string.append(track_pos[i].split("'")[3])
			# the real song is equal to the one closest to the original t
			real_track_dist = [distance(str(title), t) for title in title_string]
			indic = real_track_dist.index(min(real_track_dist))
			real_track = [track_pos[indic]]
			# use index of real track to build list of other tracks for
			# compilation of control group
			if indic > 0:
				other_tracks = track_pos[0:indic]
				if len(other_tracks) < len(track_pos):
					other_tracks.extend(track_pos[indic+1:])
			else:
				other_tracks = track_pos[1:]

		else:
			indic = 0
			if '"' in str(track_pos[0]):
				title_string = track_pos[0].split('"')[1]
			else:
				title_string = track_pos[0].split("'")[3]
			if distance(t, str(title_string)) < 5:
				real_track = [track_pos[0]]
			else:
				real_track = ''

		if real_track[0] != '':
			if '"' in real_track[0]:
				r_title = real_track[0].split('"')[1]
			else:
				r_title = real_track[0].split("'")[3]		
		# determine track number, total tracks of release, duration
		t_number = r2.findall(str(real_track[0]))[0]
		total_tracks = len([r2.findall(u) for u in track_pos])
		t_duration = track_list[indic].duration
		chart = True
		# get lyrics and metadata of other tracks if there are any
		if other_tracks:
			t_dur = [track.duration for track in track_list if str(track) != real_track]
			
			other_tracks_dict_list = []
			for i in range(0, len(other_tracks)):
				if '"' in str(other_tracks[i]):
					title = other_tracks[i].split('"')[1]
				else:
					title = other_tracks[i].split("'")[3]

				try:
					lyrics = lw.get_lyrics(a, title)
				except LyricsNotFound:
					lyrics = ''

				meta = {
				'Rank': 'N/A',
				'Artist': a,
				'Title': title,
				'Lyrics': lyrics,
				'album_name': album_name,
				'release_date': year_date,
				'total_tracks': total_tracks,
				'duration': t_dur[i],
				'track_number': r2.findall(str(other_tracks[i]))[0],
				'album_single': album_single,
				'chart': False
				}
				# returning other tracks' metadata and lyrics as a list of
				# dictionary objects
				other_tracks_dict_list.append(meta)
		
	else:
		r_title = ''
		album_name = ''
		year_date = ''
		album_single = ''
		t_number = ''
		total_tracks = ''
		t_duration = ''
		chart = ''

	# build metadata dictionary
	
	metadata = {
	'Title': r_title,
	'album_name': album_name,
	'release_date': year_date,
	'total_tracks': total_tracks,
	'duration': t_duration,
	'track_number': t_number,
	'album_single': album_single,
	'chart': chart
	}

	time.sleep(5)

	# if we have other tracks, our returned object will be a tuple of
	# charted song's metadata dictionary and other tracks' list of dictionaries
	if other_tracks_dict_list:
		return (metadata, other_tracks_dict_list)
	else:
		return metadata
