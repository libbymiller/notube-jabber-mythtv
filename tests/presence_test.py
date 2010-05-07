# run using python run_basic.py
# See http://pyxmpp.jajcus.net/trac/browser/trunk/examples/echobot.py for a more detailed example
# requires pyxmpp (on Ubuntu: sudo apt-get install python-pyxmpp)
import threading
import datetime
from threading import Timer

from pyxmpp.all import JID,Iq,Presence,Message,StreamError
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider
from pyxmpp.iq import Iq


class BasicBot(object):
  implements(IPresenceHandlersProvider)
    
  def __init__(self, client):
    self.client = client
    self.myFullJID=None


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
    print "Presence requested"
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
    content = b.get_content()
    return "iq: does nothing"


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
    return "chat message: result is nothing"

#######
# Commands
#######

  def process_command(self, cmd,param):
     print "processing command",cmd

#######
# Thread to update status
#######

  def update_presence(self):
    dtnow = datetime.datetime.now()
    dtnfmt = dtnow.strftime("%Y-%m-%d %H:%M:%S")
    jid = "not known"
    if self.client and self.client.stream:
      jid = self.client.stream.me
    p = "p:"+str(dtnfmt)+"j:"+str(jid)
    print "sending presence",p
    self.client.stream.send( Presence( status=p ) )
    t = Timer(30.0, self.update_presence)
    t.start()

