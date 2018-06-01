'''Encapsulates all the ugly link sanitization, etc'''

import json
import requests
import urllib2
from praw.models import Comment

class Link(object):
    def __init__(self, link, filetype):
        self.link = link
        self.filetype = filetype


def clean_gfycat(link):
    if "giant" in link:
        return Link(link, "mp4")
    else:
        gid = link.split('/')[-1]
        return Link(("https://giant.gfycat.com/" + gid + '.mp4'), 'mp4')

def clean_vreddit(link, comment):
    print "shortlink: " + comment.submission.shortlink
    l = urllib2.urlopen(comment.submission.shortlink)
    print l.geturl()
    r = requests.get(l.geturl() + "/.json")
    return Link(r.json()[0]["data"]["children"]["data"]["secure_media"]["reddit_video"]["fallback_url"], 'mp4')

def clean_imgur(link):
    if link.endswith('.gifv'):
        link = link.replace('.gifv', 'gif')
    else:
        code = link.split('/')[-1]
        link = "http://i.imgur.com/" + code + '.gif'
    return Link(link, 'gif')

def sanitize(text, cmnt):
    try:
        if "gfycat" in text:
            print "gfycat. " + text
            return clean_gfycat(text)
        elif "v.redd.it" in text:
            print "vreddit. " + text
            return clean_vreddit(text, cmnt)
        elif "imgur" in text:
            print "imgur. " + text
            return clean_imgur(text)
        else:
            return None
    except Exception as e:
        print e
        return None

    