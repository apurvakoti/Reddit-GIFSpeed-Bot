import imageio
import requests
import time
import json
import praw
from praw.models import Comment, Inbox, Redditor
import os
import sys
import urllib2


CONFIG = json.loads(open('gfycat.json').read())
CLIENT_ID = CONFIG["client_id"]
CLIENT_SECRET = CONFIG["client_secret"]
PAYLOAD = {
    "grant_type":"client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
  }

CMNT_TEXT = "  \n*****\n  ^^I'm ^^a ^^bot ^^| ^^Summon ^^with ^^\"/u/GIFSpeedBot ^^<speed>\" ^^| ^^[code](https://github.com/apurvakoti/Reddit-GIFSpeed-Bot) ^^| ^^[issues](https://github.com/apurvakoti/Reddit-GIFSpeed-Bot/issues)"


def get_access_token():
    r = requests.get('https://api.gfycat.com/v1/oauth/token', params=PAYLOAD)
    access_token = r.json()["access_token"]
    return {'Authorization' : 'Bearer ' + access_token}

HEADER = get_access_token()


def changespeed(vid, mult):
    print "Changing speed"
    if vid.endswith('.gifv') or vid.endswith('.gif'):
        vid = vid.replace('.gifv', '.gif')
        data = urllib2.urlopen(vid).read()
        reader = imageio.get_reader(data, 'gif')
        dur = (float(reader.get_meta_data()['duration']))
        oldfps = 1000.0 / (10 if dur == 0 else dur)
        print "old fps was " + (str(oldfps))
    
    elif vid.endswith('.mp4'):
        reader = imageio.get_reader(vid)
        oldfps = float(reader.get_meta_data()['fps'])
        
    writer = imageio.get_writer('output.mp4', fps=(oldfps*mult), quality=8.0)

    for frame in reader:
        writer.append_data(frame)
    writer.close()
    print "Done changing speed"

def upload_to_gfycat():
    print "Starting upload"
    r = requests.post('https://api.gfycat.com/v1/gfycats', headers=HEADER)
    gfykey = r.json()["gfyname"]
    data = {'key':gfykey}
    f = open('output.mp4', 'rb') #read binary data
    files = {'file':f}
    
    requests.post('https://filedrop.gfycat.com', data=data, files=files)
    status = requests.get('https://api.gfycat.com/v1/gfycats/fetch/status/' + gfykey)
    json_response = status.json()
    while json_response["task"] == "encoding":
        t = int(json_response["time"])
        time.sleep(t)
        status = requests.get('https://api.gfycat.com/v1/gfycats/fetch/status/' + gfykey)
        json_response = status.json()

    print status.text  
    if json_response["task"] == "complete":
        try:
            mp4link = json_response["mobileUrl"]
            print "Finished upload"
            return mp4link
        except:
            print "Finished upload"
            return 'https://thumbs.gfycat.com/' + json_response["gfyname"] + '-mobile.mp4'            
        
    else:
        raise "failure"

def handle_comment(cmnt):
    text = cmnt.body.lower()
    link = cmnt.submission.url
    if text == "good bot": #don't need to check parent, etc - will only be in inbox if it was a reply
        cmnt.reply("Thanks"+ CMNT_TEXT)
       
    elif link.endswith('.gif') or link.endswith('.mp4') or link.endswith('.gifv') or "gfycat.com" in link:
        print "Processing submission"
        if "gfycat.com" in link:
            gid = link.split('/')[-1]
            link = "https://giant.gfycat.com/" + gid + '.mp4'
        text = cmnt.body.lower()
        mult = float(text.split()[1])
        changespeed(link, mult)
        reply_url = upload_to_gfycat()
        cmnt.reply("Here's the GIF at "+str(mult)+"x the original speed.\n  \n[MP4 link]("+reply_url+")\n"+ CMNT_TEXT)
        print "Comment should be up"
    

def start_reddit():
    reddit = praw.Reddit('gifspeedbot')
    
    print "starting while"
    while(True):
        unread_msgs = reddit.inbox.unread(limit=None)
        for item in unread_msgs:
            if isinstance(item, Comment):
                try:
                    handle_comment(item)
                except ValueError:
                    print "value error"
                    #couldn't handle for some reason
                reddit.inbox.mark_read([item]) 

start_reddit()
