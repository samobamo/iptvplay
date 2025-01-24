import urllib.request
import gzip
import shutil
import os


def download_epg_and_playlist() -> None:
    """
    Downloads an EPG file and a playlist file, decompresses the EPG file,
    and modifies the playlist file by replacing a specific string pattern.
    """
    # Download and decompress EPG file
    epg_url = 'http://freeweb.t-2.net/itak/epg_b.xml.gz'
    epg_gz_path = 'epg.gz'
    epg_xml_path = 'epg.xml'
    urllib.request.urlretrieve(epg_url, epg_gz_path)
    with gzip.open(epg_gz_path, 'rb') as f_in, open(epg_xml_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Download playlist file
    playlist_url = 'http://freeweb.t-2.net/itak/T2_HD.m3u'
    playlist_path = 'playlist_hd.m3u'
    urllib.request.urlretrieve(playlist_url, playlist_path)

    # Modify playlist file
    inplace_change(playlist_path, 'udp://@', 'http://192.168.1.1:1234/udp/')


def inplace_change(filename, old_string, new_string):
    # Safely read the input filename using 'with'
    print(filename)
    # Read in the file
    with open(filename, 'r', encoding='utf8') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(old_string, new_string)

    # Write the file out again
    with open(filename, 'w', encoding='utf8') as file:
        file.write(filedata)
    print('done')


download_epg_and_playlist()
