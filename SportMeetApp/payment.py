import urllib.request
import hmac
import hashlib
import base64
import sys
 
post_data = {}
 
data = urllib.parse.urlencode(post_data).encode('UTF-8')
 
dig = hmac.new(b'XvsYNA0bFhTpPyfGNCVLSXoWPcoHtO', msg=data, digestmod=hashlib.sha256).digest()
post_data['ApiSignature'] = base64.b64encode(dig).decode()
post_data['instance'] = 'sportmeet'
 
data = urllib.parse.urlencode(post_data, quote_via=urllib.parse.quote).encode('UTF-8')
 
try:
    result = urllib.request.urlopen('https://api.payrexx.com/v1.0/SignatureCheck/?' + data.decode())
    sys.exit("Signature correct")
except Exception as exc:
    print(exc, file=sys.stderr)
    sys.exit("Signature wrong")