# See http://pyxmpp.jajcus.net/trac/browser/trunk/examples/echobot.py for a more detailed example
# requires pyxmpp (on Ubuntu: sudo apt-get install python-pyxmpp)
import sys
import urllib
import re
import datetime
import time
import timeit
import threading
import os
import random
import subprocess
import MySQLdb
import json
import locale
import codecs
import libxml2
import BeautifulSoup

from BeautifulSoup import BeautifulSoup

from pyxmpp import streamtls
from pyxmpp.all import JID,Iq,Presence,Message,StreamError
from pyxmpp.jabber.client import JabberClient
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider
from pyxmpp.iq import Iq


# required to talk to mythtv
#import telnetlib


class MyThread ( threading.Thread):
  def __init__ (self, pid):
     self.pid = pid
     threading.Thread.__init__ ( self )
  def run ( self ):
     print "thread run called",self.pid
     str = 'get_iplayer --pid '+self.pid+' --output="/var/lib/mythtv/recordings/" --modes=flashstd --command \'perl /home/libby/getiplayer/quickinsert.pl "<name>" "<desc>" "<duration>" "<filename>" "<pid>" "<categories>" "<channel>"\n\''
     print str
     os.system(str)

class BasicHandler(object):
  implements(IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider)
    
  def __init__(self, client):
    self.client = client
    self.nowplaying = None
    self.lastchanged=0
    self.database={}
    self.defaultpingback="http://notube:ebuton@dev.notu.be/2010/02/twitter-programmes/add"
    self.defaultrecommender="http://notube:ebuton@dev.notu.be/2010/02/recommend/foo"
    self.currentJID=None
    self.mypass = ""
    try:
       self.mypass = os.environ["MYTHMYSQLPASS"]
    except(Exception):
       print "No mysql password found (MYTHMYSQLPASS, copy it from /etc/myth/config.xml please!)"

  def get_presence_handlers(self):
     print "HELLO!!! presence heandler called"
     return [(None, self.presence)]


###????self.stream.set_presence_handler("available",self.presence)

  def presence(self,stanza):
      print "presence requested"
      status=""
      if (self.nowplaying==None):
         self.nowplaying = self.do_now_playing(False)
      if (self.nowplaying.has_key("title") and self.nowplaying.has_key("channel")):
         status = "Now playing "+self.nowplaying["title"]+" on "+self.nowplaying["channel"]
      p=Presence(
          stanza_type=stanza.get_type(),
          to_jid=stanza.get_from(),
          from_jid=stanza.get_to(),
          show=stanza.get_show(),
          status=status
          )
      print "presence ",status
      return p


  def get_iq_get_handlers(self):
    print "handlers requested for iq ",self
    return [("query","http://buttons.foaf.tv/",self.query)]

  def get_iq_set_handlers(self):
    return [] #?

  def query(self,stanza):
    body = ""
    b=stanza.get_query()
    print "GOT an IQ",str(b.get_content())
    ty=stanza.get_type()   
    rr= "no response"
    content = b.get_content()
    if b:
       b = unicode(b)
    resp = stanza.make_result_response()
    print "IQ b is ",content
    cmd = content.lower()
    if cmd == "nowp":
       body = self.html_nowp()
##more commands here
    elif cmd == "plus":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(3)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "minu":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(4)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "righ":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(2)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "left":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(1)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "okay":
       print "got command OK"
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(7)"
       resu = urllib.urlopen(uuu).read()
       # update our now playing 
       self.do_now_playing(False)
       body = self.cleanresult(resu)

    source = "<nowp-result xmlns='http://buttons.foaf.tv/'>" + body + "</nowp-result>"        
    soup = BeautifulSoup(source)
    doc = libxml2.parseDoc(str(soup.contents[0]))
    resp.set_content(doc)

    print "resp ",resp
    return resp
    
  def get_message_handlers(self):
    return [("normal", self.default)]

  def cleanresult(self, body):
     body = body.replace("<html>","")
     body = body.replace("</html>","")
     body = body.replace("<li>","")
     body = body.replace("\n","")
     return body

  def default(self,stanza):
    sub=stanza.get_subject()
    b=stanza.get_body()
    ty=stanza.get_type()
    jid=stanza.get_from()
    self.currentJID = jid
    if sub:
       sub=unicode(sub)
    if b:
       b = unicode(b)
    print "Got msg.... "+unicode(b)
    #if stanza.get_type()=="headline":
    #   # don't reply to these
    #   return True
    print "bb ",b
    arr = b.split(" ")
    cmd = arr[0]
    cmd = cmd.lower() 
    print "command ",cmd
    if cmd == "p":
       body = self.do_now_playing(False)
    elif cmd == "ev":
       body = self.do_now_playing(True)
    elif cmd == "b":
       body = self.do_bookmark()
    elif cmd == "like":
       body = self.do_bookmark()
    elif cmd == "qr":
       body = self.do_qr()
    elif cmd == "plpz":
       uuuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Pause()"
       resuu = urllib.urlopen(uuuu).read()
       body = self.cleanresult(resuu)
    elif cmd == "ffwd":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(77)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "rewd":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(78)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "menu":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=ExecBuiltIn(ActivateWindow(10024))"
       resu = urllib.urlopen(uuu).read()
#this doesn't seem to work
#       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=ExecBuiltIn(Container.Refresh())"
#       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "plus":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(3)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "minu":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(4)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "righ":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(2)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "left":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(1)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "loud":
       time.sleep(1)
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(88)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "hush":
       time.sleep(1)
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(89)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "info":
       uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(11)"
       resu = urllib.urlopen(uuu).read()
       body = self.cleanresult(resu)
    elif cmd == "nowp":
       return self.html_nowp()
    elif cmd == "save":
       pid = arr[1]
       if (re.match("^http",pid)):
          pid =pid.replace("http://www.bbc.co.uk/programmes/","")
       print "saving using get_iplayer:",pid
       MyThread(pid).start()
       body = "Trying to download "+ arr[1]
    elif cmd == "okay":
        print "got command OK"
        uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(7)"
        resu = urllib.urlopen(uuu).read()
        # update our now playing 
        self.do_now_playing(False)
        body = self.cleanresult(resu)
    elif cmd == "help":
       body = "as IQ: nowp,plus,minu,righ,left; as chat: nowp,plus,minu,righ,left,p,ev,b,qr,plpz,ffwd,rewd,menu,loud,hush,save[bbc progs url],okay,info,help"

    else:
       body = b
    msg=Message(to_jid=stanza.get_from(),from_jid=stanza.get_to(),stanza_type=stanza.get_type(),subject=sub,body=body)
    return msg


####
# Get what is playing now
####

  def do_now_playing(self,send_event):

# http://localhost:8080/xbmcCmds/xbmcHttp?command=tcurrentlyplaying
# title is gettable
# channel has to be hack parsed
# not sure about whether we nede to bother with datetime
# else we'll have to get it from the database

     title = None
     channel = None      
     uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=getcurrentlyplaying"
     resu = urllib.urlopen(uuu).read()
     results= {}

# get the title
     data = resu.split("<li>")
# look for Show Title:
     for d in data:
        if (re.match("Show Title",d)):
           title = d.replace("Show Title:","")
           title = title.replace("\n","")
           results["title"]=title
#          print title
#look for title and find the last part of it after '-'
        if (re.match("Title",d)):
           z = re.search(".* - (.*?)$",d)
           channel = z.group(1)
           print "chann ",channel
           channel = channel.replace("\n","")
           results["callsign"]=channel

     if channel!=None and title!=None:

#@@set presence
        status = "Now playing "+title+" on "+channel
        # this doesn't seem to do anything
        self.client.get_stream().send(Presence(status=status)) 
        print "sending presence",status,"..\n"
#        p=Presence(
#           stanza_type=stanza.get_type(),
#           to_jid=stanza.get_from(),
#           from_jid=stanza.get_to(),
#           show=stanza.get_show(),
#           status=status
#           )
#        self.stream.send(p)
##end send presence

        dtnow = datetime.datetime.now()
        dtnfmt = dtnow.strftime("%Y-%m-%d %H:%M:%S")

        db = MySQLdb.connect(host="localhost", user="mythtv", passwd=self.mypass,db="mythconverg")
        cursor = db.cursor()

        print "select starttime from program,channel where program.chanid=channel.chanid and starttime <= '"+dtnfmt+"' and endtime > '"+dtnfmt+"' and channel.callsign='"+channel+"' limit 1;"
        cursor.execute("select starttime from program,channel where program.chanid=channel.chanid and starttime <= '"+dtnfmt+"' and endtime > '"+dtnfmt+"' and channel.callsign='"+channel+"' limit 1;")

        result = cursor.fetchall()
        record = result[0] 
        print "RECORD",str(record)

        res2=""
        if (record!=""):
           secs = record[0]
           secsfmt = secs.strftime("%Y-%m-%d %H:%M:%S")
           results["datetime"]=secsfmt
           results["secs"]=secs-dtnow
           results["secs"]=results["secs"].seconds
           ch = channel.lower()
           ch = channel.replace(" ","")
           results["channel"]=ch

           if (re.match("bbc", ch)):
              u = "http://dev.notu.be/2009/10/bbc/info?channel="+ch
              print "u",u
              data2 = urllib.urlopen(u).read()
              results["pid"]=data2
              print data2,"...data2"
              progs = "http://www.bbc.co.uk/programmes/"
           else:
              data2=None
           if (send_event):
              print "should send event here"           
              self.send_event(results, "Watching",None)
        self.nowplaying=results
        print "returning results"
     return results

####
# send an event to the beancounter specificed by this user
####

  def send_event(self, event, e_type,user):
#    u = "http://dev.notu.be/2009/10/bbc/info?channel="+ch
#    data2 = urllib.urlopen(u).read()
    event["type"]=e_type
    jid =self.currentJID
    event["username"]=jid.node+"@"+jid.domain
    print "sending event",e_type,str(event)
    params = urllib.urlencode(event)
    f = urllib.urlopen(self.defaultpingback, params)
    ff = f.read()
    print ff

####
# Send a bookmark to delicious - requires username and password
####

  def do_bookmark(self):
    data2 = self.do_now_playing(False)
    print "got data for boomarking"
    if (data2):
      # wait one sec
      time.sleep(1)
      # do delicious on it
      uu=None
      pw=None
      if(uu!="" and pw!=""):
        progs = "http://www.bbc.co.uk/programmes/"
        progsnonbbc = "http://notube.tv/programmes/"
        delicious_url_1="https://"+uu+":"+pw+"@api.del.icio.us/v1/posts/add?url="
        if data2.has_key("pid"):
           q=progs+""+data2["pid"]+"#"+str(data2["secs"])
        else:
           titl = data2["title"]
           titl = titl.replace(" ","_")
           q=progsnonbbc+"#{titl}#"+str(data2["secs"])
        delicious_url_2=urllib.quote_plus(q)+"&description="+urllib.quote_plus(data2["title"]+" ("+str(data2["secs"])+" seconds in)")+"&tags=tv&tags=mythtv&tags=notube"
        delicious_url= delicious_url_1+delicious_url_2
        z = urllib.urlopen(delicious_url).read()
        res2= "bookmarked "+data2["title"]
        event = self.nowplaying
        if (self.nowplaying == None):
          event = {}
        jid = self.currentJID
        user = jid.node+"@"+jid.domain
        event["username"]=user
        print "sending event","Bookmarked",str(event)
        self.send_event( event, "Bookmarked", user)
##send an alert to screen
        uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=ExecBuiltIn(Notification('Bookmarked',"+data2['title']+",5))"
        resu = urllib.urlopen(uuu).read()
        res2 = self.cleanresult(resu)
      else:
        res2 = "could not bookmark "+data2["title"]+" - no username / password"
      return res2
    else:
      res2 = "no bookmark created - not playing anything at the moment"
      return res2


####
# pop up a qr code on request
####

  def do_qr(self):
    i = random.randint(1000, 9999)
    print "bot ",self.client.jid
    fn = "q"+str(i)+".png"
    jid = self.client.jid
    jstring = jid.node+"@"+jid.domain
    ar = ["qrencode", "-o", fn, "-s", "20", "xmpp:"+unicode(jstring)+"/q"+str(i)+"'"]
    print ar
    res = subprocess.Popen(ar)
    cm = ["xli", "-display", ":0.0", "-fullscreen", fn]
    time.sleep(1)
    foo = subprocess.Popen(cm)
    time.sleep(3)
    foo.terminate() 
    print foo

####
# now playing as html
###

  def html_nowp(self):
    print "nowplaying requested"
    z = self.do_now_playing(False)  
    title = None
    channel = None
    extras=""
    if z and  z.has_key("title") and z.has_key("channel"):
       title = z["title"]
       channel = z["channel"]
       pid = None
       if z.has_key("pid"):
          pid = z["pid"]
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
#            print jj

       s = "<div><meta name=\"viewport\" content=\"width=320\"/><h2>Now playing</h2><p>"+title+"</p><p>On channel: "+channel+"</p>"
       if z.has_key("starttime"):
          stt = z["starttime"]
          s = s + "<p>Programme started at: "+stt+"</p>"
       if z.has_key("channum"):
          stt = z["channum"]
          s = s + "<p>Local channel number is: "+channum+"</p>"

       s = s+"\n"+extras+"</div>"

       s = s.replace("&","&amp;")

       print "s is #{s}"
       return s
    else:
      return "<div><meta name=\"viewport\" content=\"width=320\"/><p>Nothing playing at the moment - this sometimes means it's an ad break, or else MythTV frontend has crashed</p></div>"


class Client(JabberClient):
  def __init__(self, jid, password):
    jid=JID(jid.node, jid.domain, "Basicbot")
    tls = streamtls.TLSSettings(require=True, verify_peer=False)
    auth = ['sasl:PLAIN']
    JabberClient.__init__(self, jid, password, tls_settings=tls,auth_methods=auth)
    self.interface_providers = [BasicHandler(self)]


locale.setlocale(locale.LC_CTYPE, "")
encoding = locale.getlocale()[1]
if not encoding:
    encoding = "us-ascii"
sys.stdout = codecs.getwriter(encoding)(sys.stdout, errors = "replace")
sys.stderr = codecs.getwriter(encoding)(sys.stderr, errors = "replace")


if len(sys.argv) < 3:
    print "Usage: python basicbot_pyxmpp.py jid password"
    sys.exit(1)
jid = sys.argv[1]
password = sys.argv[2]
c=Client(JID(sys.argv[1]), sys.argv[2])
c.connect()

try:
    c.loop(1)
except KeyboardInterrupt:
    c.disconnect()


