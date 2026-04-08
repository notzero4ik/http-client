import socket
import argparse
import ssl
import base64
import logging

HTTP_VERSION = "1.1"
ENCODING = "text/html"
max_redirect = 5
redirect_count = 0
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
class EmptyResponseError(Exception):
	pass

"""
Forms a HTTP request.
Parameters:
method: HTTP method (string)
host: Host header (string)
path: Path to send request to (string)
body: Payload body (string)
headers: List with custom headers (List)
Returns:
Request string.
"""
def form_request(method, host, path, body, headers):
	request = (
        f"{method} {path} HTTP/{HTTP_VERSION}\r\n"
        f"Host: {host}\r\n"
        f"Accept: {ENCODING}\r\n"
        f"Connection: close\r\n"
    )
	for i in headers:
	    request += i 
	    request += "\r\n"
	request += "\r\n"
	request += f"{body}"
	return request

"""
Parses url and returns protocol, host, path and port.
Parameters:
url: URL to parse (string)
Returns:
proto: either HTTP or HTTPS (string)
host: host from URL (string)
path: path from URL (string)
port: port from URL to connect to (int)
"""
def split_url(url):
	url = url.split("://")
	proto = url[0]
	port = 80
	path = "/"
	if proto == "https":
		port = 443
	ind = url[1].find("/")
	portind = url[1].find(":")
	if ind != -1:
		if portind != -1:
			host = url[1][:portind]
			port = url[1][portind:ind].strip(":")
			path = url[1][ind:]
		else:
			host = url[1][:ind]
			path = url[1][ind:]
	else:
		if portind != -1:
			host = url[1][:portind]
			port = url[1][portind:].strip(":")
		else:
			host = url[1]
	return proto,host,path,int(port)

"""
Sends HTTP request to provided url, parses the response from the server and returns headers, data and status code
Parameters:
method: HTTP method (string)
url: URL to send request to (string)
body: Payload body for request (string)
headers (optional): Custom headers for the request (list)
skip_ssl (optional): skips SSL certificate check, if True. Defaults to False (bool)
Returns:
response: HTTP response from the server (string)
"""
def send_request(method, url, body, headers=[], skip_ssl=False):
	proto, host, path, port = split_url(url)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	
	logger.debug(f"Connected to {host}:{port}")
	if proto == "https":
		if skip_ssl:
			logger.warning("Skipping SSL certificate check")
			context = ssl._create_unverified_context()
			s = context.wrap_socket(s, server_hostname=host)
		else:
			context = ssl.create_default_context()
			s = context.wrap_socket(s, server_hostname=host)
		logger.debug("Using HTTPS")
	request = form_request(method, host, path, body, headers)
	logger.debug(("Request:\n"
		"-------->"
	))
	logger.debug(request)
	s.sendall(request.encode("utf-8"))
	response = b""
	while True:
		data = s.recv(1024)
		if not data:
		  	break
		response += data
	response = response.decode()
	if response == "":
		raise EmptyResponseError("Server returned empty response")
	ind = response.find("\r\n\r\n")
	headers, data = response.split("\r\n\r\n")[0], response[ind:]
	return headers, data, headers.split()[1]
