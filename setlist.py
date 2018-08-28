import requests
import os
from bs4 import BeautifulSoup

if "PHISH_NET_API_KEY" in os.environ:
    apikey = os.environ["PHISH_NET_API_KEY"]
else:
     print("Must set PHISH_NET_API_KEY enviromental variable with api.phish.net key!")

def get_setlist(showdate, apikey=apikey):
    url = 'https://api.phish.net/v3/setlists/get'
    key_param = {'apikey':apikey, "showdate":showdate}
    s = requests.post(url, params=key_param)
    return s.json()

def parse_setlist(setlist):
    
    # If there is no tracklist, escape with empty response
    try:
        response_data = setlist['response']['data'][0]
    except IndexError:
        return None
        
    location = response_data['location']
    showdate = response_data['showdate']
    rating   = response_data['rating']
    venue    = BeautifulSoup(response_data['venue'],"lxml").text
    soup     = BeautifulSoup(response_data['setlistdata'],"lxml")
    
    output = []
    
    setlist  = soup.find_all(['span','a'])
    for line in setlist:
        text = line.get_text()
        is_span = line.name

        if line.name == 'span':
            which_set = line.text
        elif line.name == 'a':
            song_name = line.text
            song_url = line.attrs['href']
            if line.has_attr('title'):
                song_comment = line.attrs['title']
            else:
                song_comment = None
            track = {'set': which_set, 
                    'title': song_name ,
                    'url': song_url, 
                    'comment': song_comment,
                    'show_rating': rating,
                    'location': location,
                    'venue': venue,
                    'show_date': showdate
                    }
            output.append(track)
    return output

