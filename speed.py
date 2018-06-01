import imageio
import requests
import json
import praw
import time
from praw.models import Comment, Inbox, Redditor
import urllib
import images
import numpy as np
import links

CONFIG = json.loads(open('gfycat.json').read())
CLIENT_ID = CONFIG["client_id"]
CLIENT_SECRET = CONFIG["client_secret"]
PAYLOAD = {
    "grant_type":"client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
  }

CMNT_TEXT = "  \n*****\n  ^^Summon ^^with ^^\"/u/GIFSpeedBot ^^<speed>\" ^^| ^^[code](https://github.com/apurvakoti/Reddit-GIFSpeed-Bot) ^^| ^^I'm ^^in ^^my ^^alpha ^^stage; ^^help ^^me ^^out ^^and ^^report ^^bugs!"

#Sets up the access token for gfycat
def get_access_token():
    r = requests.post('https://api.gfycat.com/v1/oauth/token', json=PAYLOAD)
    print r.json()
    access_token = r.json()["access_token"]
    return {'Authorization' : 'Bearer ' + access_token}

HEADER = get_access_token()


def changespeed(linkObj, mult):
    print "Changing speed"

    if linkObj.filetype == "gif":
        urllib.URLopener().retrieve(linkObj.link, 'input.gif')

        reader = imageio.get_reader('input.gif', 'gif')
        dur = (float(reader.get_meta_data()['duration']))
        oldfps = 10 if dur == 0 else (1000.0/dur)
        print "old fps was " + (str(oldfps))

        frames = images.processImage('input.gif')
    
    elif linkObj.filetype == 'mp4':
        frames = list(imageio.get_reader(linkObj.link))
        oldfps = float(reader.get_meta_data()['fps'])
        
    writer = imageio.get_writer('output.mp4', fps=(oldfps*mult), quality=8.0)

    if (frames != None):
        for frame in frames:
            writer.append_data(np.array(frame))
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

#Takes in a comment, posts a reply if valid, doesn't do anything if invalid.
def handle_comment(cmnt):
    text = cmnt.body.lower()
    sub = cmnt.submission.url
    if text == "good bot": #don't need to check parent, etc - will only be in inbox if it was a reply
        cmnt.reply("Thanks"+ CMNT_TEXT)
       
    else:
        print "Processing submission"
        mult = float(text.split()[1])
        linkObj = links.sanitize(sub, cmnt)
        if not (linkObj is None):
            changespeed(linkObj, mult)
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
                except Exception as e:
                    print e
                    #couldn't handle for some reason
                reddit.inbox.mark_read([item]) 

start_reddit()
