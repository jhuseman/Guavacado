#! /usr/bin/env python

# WebRequestHandler.py
# defines:
#	WebRequestHandler
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

import importlib # using importlib for some imports to stop warnings from IDE about missing modules
guavacado_version = importlib.import_module("guavacado.version_number").guavacado_version
WebServerNameAndVer = "Guavacado/"+guavacado_version

from guavacado.misc import generate_redirect_page
# from guavacado.WebRequestHandler import WebRequestHandler
from guavacado.ConnListener import ConnListener

from datetime import datetime
import os
import fnmatch
import mimetypes
import traceback
import logging

import sys # only needed for python version check
if sys.version_info[0] < 3:
	# Python 2-specific imports and functions
	# http_server = importlib.import_module("BaseHTTPServer")
	urllib = importlib.import_module("urllib")
	url_decode = urllib.unquote
	def encode_to_send(s):
		return s
	def decode_to_str(s):
		return s
else:
	# Python 3-specific imports and functions
	# import http.server as http_server
	from urllib.parse import unquote as url_decode
	def encode_to_send(s):
		return s.encode('utf-8')
	def decode_to_str(s):
		return s.decode('utf-8')

def parse_headers(headers):
	return dict([tuple(l.split(': ',1)) for l in headers.split('\r\n') if ': ' in l])
# def get_header(headers, header_name):
# 	return parse_headers(headers).get(header_name,None)

class WebRequestHandler(object):
	'''handles requests by identifying function based on the URL, then dispatching the request to the appropriate function'''
	#TODO: figure out if host=None works from external to network
	def __init__(self, clientsocket, address, client_id, request_handler, log_handler=logging.getLogger(__name__)):
		self.clientsocket = clientsocket
		self.address = address
		self.client_id = client_id
		self.request_handler = request_handler
		self.log_handler = log_handler

		self.is_recieved = False
		self.buf = b''
	
	def handle_connection(self):
		self.recv_request()
		if self.is_recieved:
			self.send_response()

	def recv_request(self):
		try:
			self.req = self.recv_until()
			if self.req is None:
				self.log_handler.warn('Incomplete request from {addr} [id {id}]!'.format(addr=address, id=client_id))
				return
			self.head = self.recv_until(terminator=b'\r\n\r\n')
			if self.head is None:
				self.log_handler.warn('Incomplete request header from {addr} [id {id}]!'.format(addr=address, id=client_id))
				return
			self.headers = parse_headers(decode_to_str(self.head))
			self.content_length_str = self.headers.get(b'Content-Length',b'0')
			self.content_length = int(self.content_length_str)
			self.body = decode_to_str(self.recv_bytes(self.content_length))
			req_parts = self.req.replace(b'\r\n',b'').split(None,2)
			if len(req_parts) < 2:
				raise IndexError("HTTP request missing delimeters!")
			self.method_bytes, self.url_bytes = req_parts[:2]
			self.method = decode_to_str(self.method_bytes)
			self.url = decode_to_str(self.url_bytes)
			self.is_recieved = True
		except:
			self.log_handler.error('An Error was encountered while receiving the request from {addr} [id {id}]!'.format(addr=self.address, id=self.client_id))

	def send_response(self):
		try:
			self.log_handler.info('Handling request from {addr} [id {id}]: {method} {url} [body len {blen}]'.format(addr=self.address, id=self.client_id, method=self.method, url=self.url, blen=len(self.body)))
			ret_data = self.request_handler(url=self.url, method=self.method, headers=self.headers, body=self.body)
			if ret_data is None:
				self.send_header_as_code(404, url='404.html')
				self.clientsocket.sendall(encode_to_send(self.get_404_page()))
			else:
				self.send_header()
				self.clientsocket.sendall(encode_to_send(ret_data))
		except:
			self.log_handler.error('An Error was encountered while handling the request from {addr} [id {id}]!'.format(addr=self.address, id=self.client_id))
			tb = traceback.format_exc()
			self.send_header_as_code(500, url='500.html')
			self.clientsocket.sendall(encode_to_send(self.get_500_page(tb=tb)))
		
	def recv_until(self, terminator=b'\r\n', recv_size=128):
		while not terminator in self.buf:
			recv_data = self.clientsocket.recv(recv_size)
			self.buf = self.buf + recv_data
			if len(recv_data)==0:
				return None
		(ret, rem) = self.buf.split(terminator, 1)
		self.buf = rem
		return ret+terminator
	
	def recv_bytes(self, num_bytes, buf=b''):
		while len(self.buf) < num_bytes:
			recv_size = num_bytes-len(self.buf)
			recv_data = self.clientsocket.recv(recv_size)
			self.buf = self.buf + recv_data
			if len(recv_data)==0:
				self.buf = b''
				return self.buf
		ret = self.buf[:num_bytes]
		self.buf = self.buf[num_bytes:]
		return ret
	
	def send_header_as_code(self, status_code, url=None):
		"""send the header of the response with the given status code"""
		http_code_descriptions = {
			200:'OK',
			404:'Not Found',
			500:'Internal Server Error',
		}
		if url is None:
			url = self.url
		mime_url = url
		if mime_url[-1]=='/':
			mime_url = url+"index.html"
		mime_type = mimetypes.MimeTypes().guess_type(mime_url)[0]
		if mime_type is None:
			mime_type = "text/html"
		self.clientsocket.sendall(encode_to_send('HTTP/1.1 {code} {desc}\r\n'.format(code=status_code, desc=http_code_descriptions[status_code])))
		self.clientsocket.sendall(encode_to_send('Content-type: {type}\r\n'.format(type=mime_type)))
		self.clientsocket.sendall(b'\r\n\r\n')
	
	def send_header(self):
		"""send the header for a 200 status code"""
		self.send_header_as_code(200)
	
	def get_404_page(self):
		return ('<head><title>Error 404: Not Found</title></head>'+ \
		'<body><h1>Error response</h1><p>Error code 404.<p>Message: The URI "{url}" is not available.'+ \
		'<p>Error code explanation: 404 = Nothing matches the given URI.</body>').format(url=self.url)
	
	def get_500_page(self, tb=""):
		return ('<head><title>Error 500: Internal Server Error</title></head>'+ \
		'<body><h1>Error response</h1><p>Error code 500.<p>Message: The server encountered an error processing the request "{url}".'+ \
		'<p>Error code explanation: <br /> <br />{tb}</body>').format(url=self.url, tb=tb.replace('\n','<br />\n'))