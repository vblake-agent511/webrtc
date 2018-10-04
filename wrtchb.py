#
# Agent511
# vblake@agent511.com
version = '9/24/18-2'
# wrtchb.py - demo script to show WebRTC session invite via http (hosted) html refer page sent via SMS and URL for TC
#           - demo is http only and therefore only runs on Firefox (Chrome will not permit camera and mic use for http)
#           - this version (b) operates on bottle instead of flask

from opentok import OpenTok
from opentok import MediaModes
from bottle import route, run, template, error, get, post, request, ServerAdapter, static_file
import os
import sys
import requests
import ssl

# Tokbox Constants
api_key = '46165332'
api_secret = '753141f06aa40bd2e250da697dc68be672f42e09'
embed_id = '0d295073-d146-461b-bba8-72e1fffab968'

# Tokbox Embedded Room URL
# here is a sample complete url
# embed='https://tokbox.com/embed/embed/ot-embed.js?embedId=0d295073-d146-461b-bba8-72e1fffab968&room=DEFAULT_ROOM'
embed_room='DEFAULT_ROOM'
embed_url='https://tokbox.com/embed/embed/ot-embed.js?embedId='

# Agent511 SAS Enroll Constants
# here is a sample complete url
# 
sas_ok = 'SAS OK'
a511_enroll_url_base = 'http://new.a511.net/demo/SAS?cellNum='
a511_client_idpre = '&carrierID=5&action=1&clientID='
a511_clientid= '163'
a511_passpre = '&passCode='
a511_passcode = 'mst123' 

# Agent511 SAS Post Constants
# here is a sample complete url
# embed='https://tokbox.com/embed/embed/ot-embed.js?embedId=0d295073-d146-461b-bba8-72e1fffab968&room=DEFAULT_ROOM'
embed_room='DEFAULT_ROOM'
embed_url='https://tokbox.com/embed/embed/ot-embed.js?embedId='

# Agent511 WebRTC TC and User (MDN) constants
logo='logo300dpi_noreflection.jpg'

# TESTING ONLY
c_mdn = '5404542383' # Victor android
# c_mdn = '4438488386' # Victor iphone
# c_mdn = '3128600515' # Jay android
# c_mdn = '3124985501' # Jay iphone
mdn = c_mdn
web_server_ip = '34.205.84.53'
# web_server_port = '5000'
web_server_port = '5443'
plus_cc = "+1"

# TESTING ONLY
# set variables to null string before use
# this only works for demo because there is only one session at a time - do not use for multiple session
global session
session = ''
global token
token = ''

# SSL configuration
# uses self signed certificate contained in same directory as python application
# to create a server certificate, run eg
# openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
class SSLWSGIRefServer(ServerAdapter):
    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        srv = make_server(self.host, self.port, handler, **self.options)
        srv.socket = ssl.wrap_socket (
         srv.socket,
         certfile='server.pem',  # path to certificate
         server_side=True)
        srv.serve_forever()

# Agent511 logo
@route('/images/<image>')
def serve_pictures(image):
  return static_file(image, root='images/')

@route('/test')
def test():
  return "Bottle test OK"

# run(host='0.0.0.0',port=web_server_port, debug=True)

def get_mdn():
  return c_mdn

def check_mdn(mdn):
   mdn_len=len(mdn)
   print ("WRTCH: Destination address length = %d" %mdn_len)
   if mdn_len == 10:
     # if there assume there are 10 digits
     return 1
   elif mdn_len == 12: # this is an mdn in length assuming user has entered +1+MDN
     if mdn.find(pluscc):
       # if here then the +1 CC was entered, reject it
       print ("WRTCH: A +1 CC was entered.")
       return 0
   elif mdn_len < 10:
     # assume it is a shortcode
     return 0

@route("/")
def root():
  print ("WRTCH: Running " + version)
  return ("WRTCH: Running " + version)

# TESTING ONLY
@route("/stop")
def stop():
  print ("WRTCH: Stopping...")
  return sys.exit(0)

@route("/health")
def health():
  print ('WRTCH: Health OK.')
  return ("WRTCH: Health OK.")

@error(404)
def error404(error):
  return ("WRTCH: 404 Error.")

@error(500)
def error500(error):
  return ("WRTCH: 500 Error.")

# TESTING ONLY
@route("/clear")
def clear():
  session=''
  token=''
  mdn=''
  print ("WRTCH: All global and local variables cleared (reset to '')")
  return ("WRTCH: All global and local variables cleared (reset to '')")

@route("/index")
def index():
  print("WRTCH: Send Index of URLs")
  return template('index.html', mdn=mdn, image=logo)

# Tokbox Embed REST requests
# URLs MUST be called in this order
# /ecreated Creates Tokbox embed session from html entered MDN and enrolls MDN in Agent511 SAS subscription
# /erefer  Creates an HTML page with two sample (JavaScript and iframe) video windows to show the TC side
# /einvite Sends an invite for the API created session to Agent511 new.a511.net/demo/SAS

@route("/ecreate_default")
def ecreate():
  global embed
  embed=embed_url+embed_id+'&room='+embed_room
  #
  # construct the url for the erefer page -- essentially pass embed_url to ecreate (fix this later)
  global referurl
  referurl=embed
  print ("WRTCH: /ecreate: Refer URL is: " + referurl)
  #
  # return the referurl on a web page /ecreate
  return template('ecreate.html', embed_id=embed_id, mdn=mdn, embed_room=embed_room)

@get("/ecreated")
def mdn_form():
  return template('ecreated.html', embed_id=embed_id, mdn=mdn, embed_room=embed_room, referurl=referurl)

@post("/ecreated")
def ecreated():
  global embed_room
  # set the room to be empty until an MDN is entered and checked
  embed_room = ''

  global mdn
  mdn = ''
  mdn = request.forms.get('mdn')
  if check_mdn(mdn):
    print("WRTCH: MDN" + mdn + " is 10 digits as expected.")
    print ("WRTCH: /ecreated: Created embed_id: " + embed_id + " and MDN: " + mdn)
    # construct the Tokbox embed script URL
    # here is a sample complete url
    # embed='https://tokbox.com/embed/embed/ot-embed.js?embedId=0d295073-d146-461b-bba8-72e1fffab968&room=DEFAULT_ROOM'
    #
    # set the room to be the mdn
    embed_room = mdn
    print ("WRTCH: /ecreated: Embed Room: " + embed_room)
    #
    # create the embed final url from the base embed_url
    embed_url = 'https://tokbox.com/embed/embed/ot-embed.js?embedId='
    embed = embed_url + embed_id + '&room=' + embed_room
    #
    # construct the url for the erefer page -- essentially pass embed_url to ecreate (fix this later)
    global referurl
    referurl=embed
    print ("WRTCH: /ecreated: Refer URL is: " + referurl)

    # now enroll the mdn
    # use the form: http://new.a511.net/demo/SAS?cellNum=<#>&carrierID=5&action=1&clientID=163&passCode=mst123
    #                 where <#> is the mdn like 5405551212
    # reply should be "SAS OK" for server response
    # message "sub 1" goes to mdn
    print ("WRTCH: /ecreated: Enroll MDN " + mdn + " with a511.net SAS Client ID 163 and passcode " + a511_passcode)
    a511_enroll = a511_enroll_url_base + mdn + a511_client_idpre + a511_clientid + a511_passpre + a511_passcode
    print ("WRTCH: /ecreated: Enroll URL created is: " + a511_enroll)
    # post the url to Agent511 SAS
    response=requests.post(a511_enroll)
    print "WRTCH: /ecreated: Enroll MDN " + mdn + " to Agent511 SAS HTML response: ", response
    # add SAS OK check and 200 OK response code check here
  else:
    print("WRTCH: Data entered as MDN is not a valid telephone or mobile device number. Enter a 10 digit MDN.")
    # now set the mdn back to empty ''
    mdn = ''
    print("WRTCH: Embed room NOT created. Try again.")
  # return the referurl on a web page /ecreate
  return template('ecreated.html', embed_id=embed_id, mdn=mdn, embed_room=embed_room)

@route("/erefer")
def erefer():
  print("WRTCH: /erefer: Created refer URL for embed_id: " + embed_id + " and MDN: " + mdn)
  print("WRTCH: /erefer: Refer URL is: " + referurl)
  return template('erefer.html', embed_id=embed_id, mdn=mdn, embed_room=embed_room, referurl=referurl, image=logo)

@route("/einvite")
def einvite():
  posturi='http://new.a511.net/demo/SASNotify?cellNum='
  body="&body="
  closing="&clientID=163&passCode=mst123"
  #
  # construct the url to send to the MDN (caller)
  # first construct the wrtch url that points to the wrtch hosted refer web page
  wrtch_erefer_url='https://' + web_server_ip + ':' + web_server_port + '/erefer'
  #
  # second construct the url to post to Agent511 from 51511 shortcode to MDN 
  caller_url=posturi+mdn+body+wrtch_erefer_url+closing
  #
  # print the wrtch_erefer_url
  print("WRTCH: /einvite: wrtch_erefer_url: " + wrtch_erefer_url)
  #
  # print the caller_url
  print("WRTCH: /evinite: caller_url: " + caller_url)
  #
  # post the url via Agent511 to the MDN
  response=requests.post(caller_url)

  print "WRTCH: /einvite: Embed send to Agent511 HTML response: ", response
  return ("WRTCH: Tokbox embed URL sent to MDN: " + mdn)

#
# main program
#
# run(host='0.0.0.0',port=5000, debug=True)

# Setup embed URL to default
global embed
embed=embed_url+embed_id+'&room='+embed_room
# Setup embed URL to default
global referurl
referurl=embed
print ("WRTCH: main: Refer URL is: " + referurl)

# run the bottle SSL server
srv = SSLWSGIRefServer(host="0.0.0.0", port=web_server_port)
run(server=srv)
