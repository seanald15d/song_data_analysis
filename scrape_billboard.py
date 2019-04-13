import discogs as dc
import requests, re

import pandas as pd
from bs4 import BeautifulSoup
import lyricwikia as lw
from lyricwikia import LyricsNotFound


def get_metadata(a, t):

	# function to query discogs api and get metadata
    # For most cases, & tends to result in no metadata being returned
    # In fact, using just the first artist typically gets the results we want
    if '&' in a:
        a = a.split(' & ')[0]
        if ',' in a:
            a = a.split(', ')[0]
    if 'Featuring' in a:
        a = a.split(' Featuring ')[0]
    if 'with' in a:
        a = a.split(' with ')[0]
    else:
        a = a

    if '&amp;' in t:
        t = t.replace('&amp;', '&')
    else:
        t = t

    search_string = a + ' ' + t
    print('get meta ' + search_string)

    try:
        search_dict = dc.get_meta(a,t,year)
    except:
        # had to use a blanket exception here because of different ratelimiting errors
        # that I could not find discogs api's exception handler for (also catching
        # IndexError and HttpError here)
        search_dict = {
        'Title': '',
        'album_name': '',
        'release_date': '',
        'total_tracks': '',
        'duration': '',
        'track_number': '',
        'album_single': '',
        'chart': ''
        }

    return search_dict


def find_lyrics(t, a):

	# function designed to query lyricswikia api for each song. Use string methods to try our best to return lyrics
    # build empty dataframes for lyrics, metadata, and not-charted songs metadata
    df = pd.DataFrame(columns=['Rank', 'Artist', 'Lyrics'])
    m_d = pd.DataFrame(columns=['Title', 'album_name', 'release_date', 'total_tracks',
                                'duration', 'track_number', 'album_single', 'chart'])
    o_m_d = pd.DataFrame(columns=['Rank', 'Artist', 'Lyrics', 'Title',
        'album_name', 'release_date', 'total_tracks', 'duration', 'track_number',
        'album_single', 'chart'])
    # for all titles and artists, we are changing HTML &amp; to &
    # we need to massage the strings and try as hard as we can to get lyrics returned
    for i in range(0, len(t)):
        title = t[i]
        if '&amp;' in title:
            title = title.replace('&amp;', '&')
        if '&amp;' in a[i]:
            this = a[i].replace('&amp;', '&')  # Name & Name
            if this == 'Dan & Shay':
                this = 'Dan + Shay'
            try:
                lyrics = lw.get_lyrics(this, title)
                print('used this: ' + this)
                m_dict = get_metadata(this, title)
            except LyricsNotFound:
                this2 = this.split(' & ')[0]  # Name (or Name, Name)
                try:
                    lyrics = lw.get_lyrics(this2, title)
                    print('used this2: ' + this2)
                    m_dict = get_metadata(this2, title)
                except LyricsNotFound:
                    if ', ' in this2:
                        this3 = this2.split(', ')[0]  # Name or (Name Featuring Name)
                        try:
                            lyrics = lw.get_lyrics(this3, title)
                            print('used this3: ' + this3)
                            m_dict = get_metadata(this3, title)
                        except LyricsNotFound:
                            if 'Featuring' in this3:
                                this4 = this3.split(' Featuring ')[0]
                                try:
                                    lyrics = lw.get_lyrics(this4, title)
                                    print('used this4: ' + this4)
                                except LyricsNotFound:
                                    lyrics = ''
                                m_dict = get_metadata(this4, title)
                            else:
                                lyrics = ''
                                m_dict = get_metadata(this, title)
                    else:
                        lyrics = ''
                        m_dict = get_metadata(this, title)

            df = df.append({'Rank': i + 1, 'Artist': this, 'Lyrics': lyrics}, ignore_index=True)
            if isinstance(m_dict, tuple):
                m_d = m_d.append(m_dict[0], ignore_index=True)
                o_m_d = o_m_d.append(m_dict[1][0:], ignore_index=True)

            else:
                m_d = m_d.append(m_dict, ignore_index=True)

        else:
            try:
                lyrics = lw.get_lyrics(a[i], title)
                print('used natural: ' + a[i])
                m_dict = get_metadata(a[i], title)
            except LyricsNotFound:
                if 'Featuring' in a[i]:
                    this5 = a[i].split(' Featuring ')[0]
                    try:
                        lyrics = lw.get_lyrics(this5, title)
                        print('used this5: ' + this5)
                    except LyricsNotFound:
                        lyrics = ''
                    m_dict = get_metadata(this5, title)
                elif ' X ' in a[i]:
                    this6 = a[i].split(' X ')[0]
                    try:
                        lyrics = lw.get_lyrics(this6, title)
                        print('used this6: ' + this6)
                    except LyricsNotFound:
                        lyrics = ''
                    m_dict = get_metadata(this6, title)
                elif ' x ' in a[i]:
                    this7 = a[i].split(' x ')[0]
                    try:
                        lyrics = lw.get_lyrics(this7, title)
                        print('used this7: ' + this7)
                    except LyricsNotFound:
                        lyrics = ''
                    m_dict = get_metadata(this7, title)
                elif ' with ' in a[i]:
                    this8 = a[i].split(' with ')[0]
                    try:
                        lyrics = lw.get_lyrics(this8, title)
                        print('used this8: ' + this8)
                    except LyricsNotFound:
                        lyrics = ''
                    m_dict = get_metadata(this8, title)
                else:
                    lyrics = ''
                    m_dict = get_metadata(a[i], title)

            df = df.append({'Rank': i + 1, 'Artist': a[i], 'Lyrics': lyrics}, ignore_index=True)
            # if we do have charted and not-charted dfs, it comes as a tuple
            if isinstance(m_dict, tuple):
                m_d = m_d.append(m_dict[0], ignore_index=True)
                o_m_d = o_m_d.append(m_dict[1][0:], ignore_index=True)

            else:
                m_d = m_d.append(m_dict, ignore_index=True)

    return df, m_d, o_m_d


def clean_list(title, artist):

	# clean artist and title info

    titles = []
    for i in title:
        temp = i.split('\n')
        titles.append(temp[1])

    artists = []
    for j in artist:
        temp = j.split('\n')
        if len(temp) > 3:
            artists.append(temp[2])
        else:
            artists.append(temp[1])

    df, m_d, o_m_d = find_lyrics(titles, artists)
    return df, m_d, o_m_d


def scrape_page(url):
	
	# function to scrape each page for artist and title information

    r = requests.get(url)
    html_doc = r.text

    soup = BeautifulSoup(html_doc, features='html.parser')

    title = soup.find_all('a', {'itemprop': 'name'})
    artist = soup.find_all('a', {'class': 'artist'})
    
    ts = []
    for t in title:
        ts.append(str(t))

    a = []
    for ar in artist:
        a.append(str(ar))

    df, m_d, o_m_d = clean_list(ts, a)

    return df, m_d, o_m_d


if __name__ == '__main__':
	# create list of years to scrape song chart data for
    years = range(1960, 2010)

    # iterate over list and build lyrics and metadata dataframes to push to csv
    for year in years:
	    df, m_d, o_m_d = scrape_page('https://playback.fm/charts/country/' + str(year))
	    result = pd.concat([df, m_d], axis=1, join_axes=[df.index])
	    final = result.append(o_m_d, ignore_index=True)

	    final.to_csv('song_charts\\playback_meta_data' + '_' + str(year) + '.csv')