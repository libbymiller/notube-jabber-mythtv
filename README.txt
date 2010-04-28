Various bots to talk to media centres.

Use 

python run_basic.py jid pwd (to run buttons_pyxmpp_bot_stub.py a stub that only requires pyxmpp and libxml2)
python run_myth.py jid pwd (to run mythtv_pyxmpp_bot.py for mythtv)
python run_xbmc.py jid pwd (to run xbmc_pyxmpp_bot.py for xbmc)

xbmc_pyxmpp_bot.py and mythtv_pyxmpp_bot.py both use buttons_pyxmpp_bot_stub.py

do this:

export MYTHMYSQLPASS=asdasfwsgehedh 
export NOTUBEDELICIOUSPASS=lkjglkxfgf

i.e. your passwords. delicious username is hardcoded as 'notube'
