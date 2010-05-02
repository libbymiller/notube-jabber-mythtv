# run using python run_basic.py
# See http://pyxmpp.jajcus.net/trac/browser/trunk/examples/echobot.py for a more detailed example
# requires pyxmpp (on Ubuntu: sudo apt-get install python-pyxmpp)
import sys
import urllib
import re
import time
import threading
import random
import json
import libxml2
import datetime
import BeautifulSoup
from threading import Timer

from BeautifulSoup import BeautifulSoup

from pyxmpp.all import JID,Iq,Presence,Message,StreamError
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider
from pyxmpp.iq import Iq


class BasicBot(object):
  implements(IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider)
    
  def __init__(self, client):
    self.client = client
    self.nowplaying = None

    # this is the time in secs to wait between querying what's on
    # we don't want to overload, say, mythtv
    # not used in the stub bot
    self.time_to_wait = 60
    now = datetime.datetime.now()
    difference1 = datetime.timedelta(seconds = self.time_to_wait+10)
    self.lastchanged = datetime.datetime.now() - difference1

    # how often in secs we send changes in presence
    # should have some relationship with self.time_to_wait
    # it launches a thread that updates presence ever n secs
    self.time_to_update_presence = 60

    self.database={}
    self.defaultpingback=None
    self.defaultrecommender=None
    self.currentJID=None
    self.myFullJID=None
    self.mypass = None


######
# Various interfaces so we can handle presence, iq and chat messages
######

  def get_presence_handlers(self):
     print "Presence handlers called"
     return [(None, self.presence)]

  def get_iq_get_handlers(self):
    print "get handlers requested for iq"
    return [("query","http://buttons.foaf.tv/",self.iq)]

  def get_iq_set_handlers(self):
    print "set handlers requested for iq"
    return [("query","http://buttons.foaf.tv/",self.iq)]

  def get_message_handlers(self):
    return [("normal", self.default)]

######
# handle presence messages
######

  def presence(self,stanza):
      print "Presence requested - starting the thread"

# do full jid here - seems as good a place as any
      if self.client and self.client.stream:
        self.myFullJID = self.client.stream.me

# start the presence thread
#     self.update_presence(stanza)
      #check we are up to date
      self.update_presence()

######
# Handle iq messages
######

  def iq(self,stanza):
    print "IQ requested"
    print "iq stanza",stanza.serialize(),"\n"
    b=stanza.get_query()
    print "GOT an IQ",str(b.get_content())," ",self.myFullJID
    ty=stanza.get_type()   
    rr= "no response"
    content = b.get_content()
    if b:
       b = unicode(b)
    resp = stanza.make_result_response()
    cmd = content.lower()
    body = ''
# These commands are the ones that we want to use over IQ
    param=None
    arr = cmd.split(" ")
    if(arr and len(arr)>1 and arr[1]):
       cmd = arr[0]
       param = arr[1]
    body = self.process_command(cmd,param)
    source = "<nowp-result xmlns='http://buttons.foaf.tv/'>" + body + "</nowp-result>"        
    soup = BeautifulSoup(source)
    doc = libxml2.parseDoc(str(soup.contents[0]))
    resp.set_content(doc)
    #print "IQ response is ",resp
    return resp


######
# Handle chat messages
######

  def default(self,stanza):
    sub=stanza.get_subject()
    print "chat stanza",stanza.serialize(),"\n"
    b=stanza.get_body()
    ty=stanza.get_type()
    jid=stanza.get_from()
    self.currentJID = jid
    if sub:
       sub=unicode(sub)
    if b:
       b = unicode(b)
    print "Got chat message.... "+unicode(b)
    #if stanza.get_type()=="headline":
    #   # don't reply to these
    #   return True
    arr = b.split(" ")
    cmd = arr[0]
    cmd = cmd.lower() 
    print "Chat command is ",cmd
    param=None
    if(len(arr)>1 and arr[1]):
       param = arr[1]

    body = self.process_command(cmd, param)
    msg=Message(to_jid=stanza.get_from(),from_jid=stanza.get_to(),stanza_type=stanza.get_type(),subject=sub,body=body)
    return msg

#######
# Commands
#######

  def process_command(self, cmd,param):
    if cmd == "nowp":
       body = self.html_nowp()
    elif cmd == "plus":
       body = self.plus()
    elif cmd == "minu":
       body = self.minu()
    elif cmd == "righ":
       body = self.righ()
    elif cmd == "left":
       body = self.left()
    elif cmd == "like":
       body = self.do_bookmark()
    elif cmd == "qr":
       body = self.do_qr()
    elif cmd == "plpz":
       body = self.plpz()
    elif cmd == "ffwd":
       body = self.ffwd()
    elif cmd == "rewd":
       body = self.rewd()
    elif cmd == "menu":
       body = self.menu()
    elif cmd == "info":
       body = self.info()
    elif cmd == "loud":
       body = self.loud()
    elif cmd == "hush":
       body = self.hush()
    elif cmd == "save":
       body = self.save(param)
    elif cmd == "okay":
       body = self.okay()
    elif cmd == "help":
       body = self.help()
    else:
       body = cmd
    print "returning body",body
#    print body.__class__
    return body

#####
# These commands need to be made specific to the platform
# These are just stubs
#####

  def plus(self):
    return "plus called",self.myFullJID

  def minu(self):
    return "minu called",self.myFullJID

  def righ(self):
    return "righ called",self.myFullJID

  def left(self):
    return "left called",self.myFullJID

  def plpz(self):
    return "plpz called",self.myFullJID

  def ffwd(self):
    return "ffwd called",self.myFullJID

  def rewd(self):
    return "rewd called",self.myFullJID

  def menu(self):
    return "menu called",self.myFullJID

  def info(self):
    return "info called",self.myFullJID

  def loud(self):
    return "loud called",self.myFullJID

  def hush(self):
    return "hush called",self.myFullJID

  def okay(self):
    return "okay called",self.myFullJID


#####
# Help message
#####

  def help(self):
     body = "nowp,plus,minu,righ,left,like,qr,plpz,ffwd,rewd,menu,loud,hush,save [bbc progs url],okay,info,help"
     return body

#####
# Save using the iplayer thread
#####

  def save(self,pid):
     body = None
     if pid:
        if (re.match("^http",pid)):
           pid =pid.replace("http://www.bbc.co.uk/programmes/","")
        pid_match = re.match('.*?\/?([b-df-hj-np-tv-z][0-9b-df-hj-np-tv-z]{7,15}).*?',pid)
        if pid_match:
           pid = pid_match.group(1)
           print "saving using get_iplayer:",pid
           GetIplayerThread(pid).start()
           body = "Trying to download "+ pid
        else:
          body = "No pid found"
     else:
          body = "No pid found"
     return body


####
# Get what is playing now - faked!
####

  def do_now_playing(self,send_event,force=False):
    # force forces an update if there's any wait set normally
    # not implemented here
    print "nowp called",self.myFullJID

    results = {'title': "BBC News At Six", 'pid': 'b00s1kpc', 'datetime': '2010-04-13T18:00:00', 'secs': 600, 'channum': '1001', 'channel': 'bbcone'}
    if (send_event):
       print "Should send watching event here"           
       self.send_event(results, "Watching")

    self.nowplaying=results


######
# presence update methods
######

  def get_status(self):
    if (self.nowplaying and self.nowplaying.has_key("title") and self.nowplaying.has_key("channel")):
       status = "Now playing "+self.nowplaying["title"]+" on "+self.nowplaying["channel"]
    else:
       status = "Nothing playing at the moment"
    dtnow = datetime.datetime.now()
    dtnfmt = dtnow.strftime("%Y-%m-%d %H:%M:%S")
    jid = "not known"
    if self.client and self.client.stream:  
      jid = self.client.stream.me
    status = "p:"+str(dtnfmt)+"j:"+str(jid)+" "+status
    return status


  def update_presence(self):
    print "update presence called"

    self.do_now_playing(False)
    time.sleep(2)
    status = self.get_status()
    self.client.stream.send( Presence( status=status ) )
    print "sending presence",status
    t = Timer(self.time_to_update_presence, self.update_presence)
    t.start()


######
# cases where we just call this once
# no timer starts
######

  def update_presence_once(self,stanza=None):

    self.do_now_playing(False, True) #force it to update

    status = self.get_status()
    print "[1]sending presence",status
    if self.client and self.client.stream:  
      self.client.stream.send( Presence( status=status ) )
    else:
      print "not sending status because no client" 


####
# Send an event to the beancounter specified by this user
####

  def send_event(self, event, e_type):
    event["type"]=e_type
    jid =self.myFullJID
#   event["username"]=jid.node+"@"+jid.domain #crashes sometimes
    print "sending event",e_type,str(event)


####
# Send a bookmark to delicious - requires username and password
####


  def do_bookmark(self):
    print "bookmark called",self.myFullJID
    self.do_now_playing(False)
    data2 = self.nowplaying
    print "got data for bookmarking", data2
    res2= "bookmarked "+data2["title"]
    self.send_event( data2, "Bookmarked")
    print "Sending alert to screen"
    return res2


####
# Pop up a qr code on request
####

  def do_qr(self):
    pin = random.randint(1000, 9999)
    fn = "q"+str(pin)+".png"
    jstring = str(self.myFullJID)
    print "bot ",jstring
# Need to add some stuff so that we can accept things with this pin
    return "Popping up a QR code for"+jstring+"#"+str(pin)," ",self.myFullJID

####
# Now playing as html
###

  def html_nowp(self):
    print "nowplaying requested",self.myFullJID
    self.do_now_playing(False) 
    z = self.nowplaying
    print "z ",z 
    if z:
      title = z["title"]
      channel = z["channel"]
      channum = None
      stt = z["datetime"]
      if z.has_key("channum"):
         channum = z["channum"]
      extras = ""
# get the pid if it's a BBC programme
      if (re.match("bbc", channel)):
         u = "http://dev.notu.be/2009/10/bbc/info?channel="+channel
         pid = urllib.urlopen(u).read()
         print "u",u,"pid",pid

# query chris' stff
# http://services.notube.tv/epg/datawarehouse.php?service=getannotation&pid=b00c4frc
         if (pid):
            uu = "http://services.notube.tv/epg/datawarehouse.php?service=getannotation&pid="+pid
            j = urllib.urlopen(uu).read()
            jj = json.loads(j)
            for x in jj:
               for k, v in x.items():
                  if (k=="name" and v =="Actor"):
                     extras=extras+ "Actor: <a href='"+x["URL"]+"'>"+x["value"]+"</a><br />"
                  elif (k=="name" and v =="Director"):
                     extras=extras+ "Director: <a href='"+x["URL"]+"'>"+x["value"]+"</a><br />"
                  elif (k=="name" and v=="dbpprop:abstract"):
                     extras=extras+ "Description: "+x["value"]+"<br />"
                  elif (k=="name" and v=="skos:subject"):
                     cat = x["value"]
                     extras=extras+ "Category: <a href='"+cat+"'>"+cat+"</a><br />"

      s = "<div><meta name=\"viewport\" content=\"width=320\"/><h2>Now playing</h2><p>"+title+"</p><p>On channel: "+channel+"</p><p>Programme started at: "+stt+"</p>"
      if (channum):
         s = s+"<p>Local channel number is: "+channum+"</p>"
      s = s+extras+"</div>"

      s = s.replace("&","&amp;")

      print "s is ",s
      return s
    else:
      return "<div><meta name=\"viewport\" content=\"width=320\"/><p>Nothing playing at the moment - this sometimes means it's an ad break, or else MythTV frontend has crashed</p></div>"



######
# Special thread for getiplayer
######

class GetIplayerThread ( threading.Thread):
  def __init__ (self, pid):
     self.pid = pid
     threading.Thread.__init__ ( self )
  def run ( self ):
     print "getIplayer thread run called",self.pid," ",self.myFullJID


