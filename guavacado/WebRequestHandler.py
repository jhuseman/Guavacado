#! /usr/bin/env python

from .misc import init_logger, addr_rep

import mimetypes
import traceback
import socket

def parse_headers(headers):
	return dict([tuple(l.split(': ',1)) for l in headers.split('\r\n') if ': ' in l])

class WebRequestHandlingException(Exception):
	'''base class for all exceptions related to web requests'''
	pass

class RequestTimedOut(WebRequestHandlingException):
	'''indicates there was a timeout receiving required data'''
	pass

class IncompleteRequest(WebRequestHandlingException):
	'''indicates not enough data was received with the request'''
	pass

class IncompleteRequestHeader(WebRequestHandlingException):
	'''indicates the request header was not terminated properly'''
	pass

class IncorrectRequestSyntax(WebRequestHandlingException):
	'''indicates the syntax of the main request line was incorrect'''
	pass

class WebRequestHandler(object):
	'''handles requests by identifying function based on the URL, then dispatching the request to the appropriate function'''
	#TODO: figure out if host=None works from external to network
	def __init__(self, clientsocket, address, client_id, request_handler, timeout=None):
		self.log_handler = init_logger(__name__)
		self.clientsocket = clientsocket
		self.address = address
		self.client_id = client_id
		self.request_handler = request_handler
		self.clientsocket.settimeout(timeout)

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
				raise IncompleteRequest()
			self.head = self.recv_until(terminator=b'\r\n\r\n')
			if self.head is None:
				raise IncompleteRequestHeader()
			self.headers = parse_headers(self.head.decode('utf-8'))
			self.content_length_str = self.headers.get(b'Content-Length',b'0')
			self.content_length = int(self.content_length_str)
			self.body = self.recv_bytes(self.content_length).decode('utf-8')
			req_parts = self.req.replace(b'\r\n',b'').split(None,2)
			if len(req_parts) < 2:
				raise IncorrectRequestSyntax()
			self.method_bytes, self.url_bytes = req_parts[:2]
			self.method = self.method_bytes.decode('utf-8')
			self.url = self.url_bytes.decode('utf-8')
			self.is_recieved = True
		except RequestTimedOut:
			self.log_handler.info('{addr} [id {id}] Request timed out!'.format(addr=addr_rep(self.address), id=self.client_id))
		except IncompleteRequestHeader:
			self.log_handler.error('{addr} [id {id}] Incomplete request header!'.format(addr=addr_rep(self.address), id=self.client_id))
		except IncompleteRequest:
			self.log_handler.error('{addr} [id {id}] Incomplete request!'.format(addr=addr_rep(self.address), id=self.client_id))
		except:
			self.log_handler.error('{addr} [id {id}] An Error was encountered while receiving the request!'.format(addr=addr_rep(self.address), id=self.client_id))

	def send_response(self):
		try:
			self.log_handler.info('{addr} [id {id}] Handling request: {method} {url} [body len {blen}]'.format(addr=addr_rep(self.address), id=self.client_id, method=self.method, url=self.url, blen=len(self.body)))
			ret_data = self.request_handler(url=self.url, method=self.method, headers=self.headers, body=self.body)
			if ret_data is None:
				self.send_header_as_code(404, url='404.html')
				self.clientsocket.sendall(self.get_404_page().encode('utf-8'))
			else:
				self.send_header()
				self.clientsocket.sendall(ret_data.encode('utf-8'))
		except:
			self.log_handler.warn('{addr} [id {id}] An Error was encountered while handling the request!'.format(addr=addr_rep(self.address), id=self.client_id))
			tb = traceback.format_exc()
			try:
				self.send_header_as_code(500, url='500.html')
				self.clientsocket.sendall(self.get_500_page(tb=tb).encode('utf-8'))
			except:
				self.log_handler.error('{addr} [id {id}] An Error was encountered while attempting to send a 500 Error response!'.format(addr=addr_rep(self.address), id=self.client_id))
		
	def recv_until(self, terminator=b'\r\n', recv_size=128):
		try:
			while not terminator in self.buf:
				recv_data = self.clientsocket.recv(recv_size)
				self.buf = self.buf + recv_data
				if len(recv_data)==0:
					return None
		except socket.timeout:
			raise RequestTimedOut()
		(ret, rem) = self.buf.split(terminator, 1)
		self.buf = rem
		return ret+terminator
	
	def recv_bytes(self, num_bytes, buf=b''):
		try:
			while len(self.buf) < num_bytes:
				recv_size = num_bytes-len(self.buf)
				recv_data = self.clientsocket.recv(recv_size)
				self.buf = self.buf + recv_data
				if len(recv_data)==0:
					self.buf = b''
					return self.buf
		except socket.timeout:
			raise RequestTimedOut()
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
		self.clientsocket.sendall('HTTP/1.1 {code} {desc}\r\n'.format(code=status_code, desc=http_code_descriptions[status_code]).encode('utf-8'))
		self.clientsocket.sendall('Content-type: {type}\r\n'.format(type=mime_type).encode('utf-8'))
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
