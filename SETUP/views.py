import hmac
from hashlib import sha1
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_bytes
import sys
import subprocess

import requests
from ipaddress import ip_address, ip_network

@csrf_exempt
def pull(request):
    '''
    # Verify if request came from GitHub
    forwarded_for = u'{}'.format(request.META.get('HTTP_X_FORWARDED_FOR'))
    remote_addr = u'{}'.format(request.META.get('REMOTE_ADDR'))
    addr_to_use = 'test'
    
    if remote_addr == '127.0.0.1':
        addr_to_use = forwarded_for
    else:
        addr_to_use = remote_addr
    
	# client_ip_address = ip_address(forwarded_for)
    client_ip_address = ip_address(addr_to_use)
    whitelist = requests.get('https://api.github.com/meta').json()['hooks']

    for valid_ip in whitelist:
        if client_ip_address in ip_network(valid_ip):
            break
    else:
        return HttpResponseForbidden('Permission denied.')

    header_signature = request.META.get("HTTP_X_HUB_SIGNATURE")
    if header_signature is None:
        return HttpResponseForbidden('Permission denied.')
    
    sha_name, signature = header_signature.split('=')
    if sha_name != 'sha1':
        return HttpResponseServerError('Operation not supported.', status=501)
    
    mac = hmac.new(force_bytes(settings.GITHUB_WEBHOOK_KEY), msg=force_bytes(request.body), digestmod=sha1)
    if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
        return HttpResponseForbidden('Permission denied.')
    '''
    # Process the GitHub events
    event = request.META.get('HTTP_X_GITHUB_EVENT', 'ping')

    print >>sys.stderr, 'Beginning pull from the Github!'
    subprocess.call("/home/dhickman/APIS/pull.sh")
    print >>sys.stderr, 'Done!'
    return HttpResponse('success')
    '''
    if event == 'ping':
        print >>sys.stderr, 'Beginning pull from the DB!'
        subprocess.call("/home/dhickman/pull.sh")
        print >>sys.stderr, 'Done!'

        return HttpResponse('pong')
    elif event == 'push':
        print >>sys.stderr, 'Beginning pull from the DB!'
        subprocess.call("/home/dhickman/pull.sh")
        print >>sys.stderr, 'Done!'
        # Do something...
        return HttpResponse('success')
    '''
    # In case we receive an event that's neither a ping or push
    return HttpResponse(status=204)