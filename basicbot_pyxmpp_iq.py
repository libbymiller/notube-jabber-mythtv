# See http://pyxmpp.jajcus.net/trac/browser/trunk/examples/echobot.py for a more detailed example
# requires pyxmpp (on Ubuntu: sudo apt-get install python-pyxmpp)
import sys

from pyxmpp import streamtls
from pyxmpp.all import JID,Iq,Presence,Message,StreamError
from pyxmpp.jabber.client import JabberClient
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider,IIqHandlersProvider

class BasicHandler(object):
  implements(IMessageHandlersProvider)
    
  def __init__(self, client):
    self.client = client

  def get_iq_get_handlers(self):
    print "handlers requested for iq ",self
    return [("buttons","http://buttons.foaf.tv/",self.query)]

  def get_iq_set_handlers(self):
    return [] #?

  def query(self,stanza):
    print "XXXX[1]ok"
    sub=stanza.get_subject()
    b=stanza.get_body()
    print "GOT an IQ",str(b)
    ty=stanza.get_type()
    if sub:
       sub=unicode(sub)
    if b:
       b = unicode(b)
    resp=iq.make_result_response()
    resp.set_content("hello")   
    return iq   
    
  def get_message_handlers(self):
    return [("normal", self.default)]

  def default(self,stanza):
    sub=stanza.get_subject()
    b=stanza.get_body()
    ty=stanza.get_type()
    if sub:
       sub=unicode(sub)
    if b:
       b = unicode(b)
    print "Got msg "+unicode(b)
    if stanza.get_type()=="headline":
       # don't reply to these
       return True
    msg=Message(to_jid=stanza.get_from(),from_jid=stanza.get_to(),stanza_type=stanza.get_type(),subject=sub,body="Hello! "+unicode(stanza.get_from()))
    return msg

class Client(JabberClient):
  def __init__(self, jid, password):
    jid=JID(jid.node, jid.domain, "Basicbot")
    tls = streamtls.TLSSettings(require=True, verify_peer=False)
    auth = ['sasl:PLAIN']
    JabberClient.__init__(self, jid, password, tls_settings=tls,auth_methods=auth)
    self.interface_providers = [BasicHandler(self)]

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

