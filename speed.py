import imageio
import requests
import time
import json
import praw
from praw.models import Comment, Inbox
import os
import sys


CONFIG = json.loads(open('gfycat.json').read())
CLIENT_ID = CONFIG["client_id"]
CLIENT_SECRET = CONFIG["client_secret"]
PAYLOAD = {
    "grant_type":"client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
  }


def get_access_token():
    r = requests.get('https://api.gfycat.com/v1/oauth/token', params=PAYLOAD)
    access_token = r.json()["access_token"]
    return {'Authorization' : 'Bearer ' + access_token}

HEADER = get_access_token()


def changespeed(vid, mult):
    print "Changing speed"
    reader = imageio.get_reader(vid)
    oldfps = reader.get_meta_data()['fps']
    writer = imageio.get_writer('output.mp4', fps=(oldfps*mult))
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

        

    mp4link = json_response["mp4Url"]
    print "Finished upload"
    return mp4link

def handle_comment(cmnt):
    text = cmnt.body.lower()
    link = cmnt.submission.url
    if link.endswith('.gif') or link.endswith('.mp4'):
        print "Processing submission"
        link = link.replace('.gif', '.mp4')
        text = cmnt.body.lower()
        mult = float(text.split()[1])
        changespeed(link, mult)
        reply_url = upload_to_gfycat()
        cmnt.reply("Here's the GIF at "+mult+"x the original speed.\n  \n[MP4 link]("+reply_url+")\n  \n*****\n  ^^I'm ^^a ^^bot ^^| ^^Summon ^^with ^^\"/u/GIFSpeedBot ^^<speed>\" ^^| ^^[code](https://github.com/apurvakoti/Reddit-GIFSpeed-Bot))
        print "Comment should be up"
    

def start_reddit():
    reddit = praw.Reddit('gifspeedbot')
    subreddit = reddit.subreddit("bottesting")
    
    print "starting while"
    while(True):
        unread_msgs = reddit.inbox.unread(limit=None)
        for item in unread_msgs:
            if isinstance(item, Comment):
                try:
                    handle_comment(item)
                except ValueError:
                    pass #couldn't handle for some reason
                reddit.inbox.mark_read([item])

                


start_reddit()












