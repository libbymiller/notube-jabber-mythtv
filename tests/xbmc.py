import urllib
import re

uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=getcurrentlyplaying"
resu = urllib.urlopen(uuu).read()
# get the title
data = resu.split("<li>")
# look for Show Title:
for d in data:
   if (re.match("Show Title",d)):
       z = d.replace("Show Title:","")
       print z
#look for title and find the last part of it after '-'
   if (re.match("Title",d)):
       z = re.search(".* - (.*?)$",d)
       print z.group(1)

#print data
