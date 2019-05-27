#! /usr/bin/env python

# WebRequestHandler.py
# defines:
#	WebRequestHandler
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

import importlib # using importlib for some imports to stop warnings from IDE about missing modules

import mimetypes
import traceback

import sys # only needed for python version check
if sys.version_info[0] < 3:
	# Python 2-specific imports and functions
	http_server = importlib.import_module("BaseHTTPServer")
	def encode_to_send(s):
		return s
	def get_header(headers, header_name):
		return headers.getheader(header_name)
else:
	# Python 3-specific imports and functions
	import http.server as http_server
	def encode_to_send(s):
		return s.encode('UTF-8')
	def parse_headers(headers):
		return dict([tuple(l.split(': ')[:2]) for l in str(headers).split('\n') if ': ' in l])
	def get_header(headers, header_name):
		return parse_headers(headers).get('Content-Length',None)

class WebRequestHandler(http_server.BaseHTTPRequestHandler):
	'''the internal request handler used by python's http_server'''
	def send_header_as_code(self, status_code, url):
		"""send the header of the response with the given status code"""
		mime_url = url
		if mime_url[-1]=='/':
			mime_url = url+"index.html"
		mime_type = mimetypes.MimeTypes().guess_type(mime_url)[0]
		if mime_type is None:
			mime_type = "text/html"
		self.send_response(status_code)
		self.send_header("Content-type", mime_type)
		self.end_headers()
	
	def do_HEAD(self):
		"""Respond to a HEAD request."""
		self.send_header_as_code(200, self.path)
	
	def GENERAL_REQ_HANDLER(self,callback):
		"""Respond to a GET request."""
		body_len_str = get_header(self.headers, 'Content-Length')
		if body_len_str is None:
			body_len = 0
			body = None
		else:
			body_len = int(body_len_str)
			body = self.rfile.read(body_len)
		try:
			ret_data = callback(url=self.path, method=self.command, headers=self.headers, body=body)
			if ret_data is None:
				self.send_header_as_code(404, '404.html')
				self.wfile.write(encode_to_send(self.get_404_page(url=self.path)))
			else:
				self.do_HEAD()
				self.wfile.write(encode_to_send(ret_data))
		except:
			tb = traceback.format_exc()
			self.send_header_as_code(500, '500.html')
			self.wfile.write(encode_to_send(self.get_500_page(tb=tb, url=self.path)))
	
	def log_message(self, format, *args):
		if not self.log_string is None:
			self.log_string("%s - - [%s] %s" %
				(self.client_address[0],
				self.log_date_time_string(),
				format%args))
	
	def log_string(self, data):
		print(data)
	
	def get_404_page(self, url=""):
		return ('<head><title>Error 404: Not Found</title></head>'+ \
		'<body><h1>Error response</h1><p>Error code 404.<p>Message: The URI "{url}" is not available.'+ \
		'<p>Error code explanation: 404 = Nothing matches the given URI.</body>').format(url=url)
	
	def get_500_page(self, tb="", url=""):
		return ('<head><title>Error 500: Internal Server Error</title></head>'+ \
		'<body><h1>Error response</h1><p>Error code 500.<p>Message: The server encountered an error processing the request "{url}".'+ \
		'<p>Error code explanation: <br /> <br />{tb}</body>').format(url=url, tb=tb.replace('\n','<br />\n'))
	
