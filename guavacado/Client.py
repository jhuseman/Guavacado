#! /usr/bin/env python

import socket
import ssl
import threading

from .misc import addr_rep, init_logger
from .WebRequestHandler import WebRequestHandler

class Client(object):
	'''
	allows connections to be made as a client
	'''
	def __init__(self, addr='localhost', port=80, TLS=False, UDP=False, disp_type='web', TLS_check_cert=True):
		self.log_handler = init_logger(__name__)
		self.addr = addr
		self.port = port
		self.TLS = TLS
		self.UDP = UDP
		self.disp_type = disp_type
		self.TLS_check_cert = TLS_check_cert
	
	@staticmethod
	def from_url(url, TLS_check_cert=True):
		prot_split = url.split('://',1)
		if len(prot_split)>1:
			protocol = prot_split[0]
			url_noprot = prot_split[1]
		else:
			protocol = 'http'
			url_noprot = url
		if protocol.lower() in ['https']:
			TLS = True
		else:
			TLS = False
		host_port_split = url_noprot.split('/',1)
		if len(host_port_split)>1:
			host_port = host_port_split[0]
			resource = '/'+host_port_split[1]
		else:
			host_port = url_noprot
			resource = '/'
		host_split = host_port.split(':',1)
		if len(host_split)>1:
			host = host_split[0]
			try:
				port = int(host_split[1])
			except ValueError:
				host = host_port
				if TLS:
					port = 443
				else:
					port = 80
		else:
			host = host_port
			if TLS:
				port = 443
			else:
				port = 80
		
		return (Client(addr=host, port=port, TLS=TLS, disp_type='web', TLS_check_cert=TLS_check_cert), resource)
	
	@staticmethod
	def request_url(url, method='GET', body=None, TLS_check_cert=True):
		c, r = Client.from_url(url, TLS_check_cert=TLS_check_cert)
		return c.request_web(resource=r, method=method, body=body)
	
	def connect_socket(self):
		'''creates a socket connection to the server'''
		self.log_handler.debug('making connection to {addr}.'.format(addr=addr_rep({'addr':self.addr, 'port':self.port, 'TLS':self.TLS, 'UDP':self.UDP})))
		if self.TLS:
			tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
			# tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
			if self.TLS_check_cert:
				tls_context.verify_mode = ssl.CERT_REQUIRED
				tls_context.check_hostname = True
			else:
				tls_context.check_hostname = False
				tls_context.verify_mode = ssl.CERT_NONE
			tls_context.load_default_certs()
			raw_sock = socket.socket(socket.AF_INET)
			sock = tls_context.wrap_socket(raw_sock, server_hostname=self.addr)
		elif self.UDP:
			# create an INET, DATAGRAM (UDP) socket
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		else:
			# create an INET, STREAMing (TCP) socket
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((self.addr, self.port))
		return sock

	def close_socket(self, sock):
		sock.shutdown(socket.SHUT_RDWR)
		sock.close()
	
	def request_web(self, resource='/', method='GET', body=None):
		'''makes a web request and returns the body of the response'''
		ret = []
		ret_event = threading.Event()
		def req_callback(body, code, ret=ret, ret_event=ret_event):
			ret.append((body, code))
			ret_event.set()
		self.request_web_async(req_callback, resource=resource, method=method, body=body)
		ret_event.wait()
		return ret[0]

	def request_web_async(self, callback, resource='/', method='GET', body=None, timeout=None):
		'''makes a web request using the raw socket and returns the body of the response'''
		sock = self.connect_socket()
		# buf = b''

		req_handler = WebRequestHandler(sock, (self.addr, self.port), None, callback, timeout=timeout, is_client=True, client_resource=resource, client_body=body, client_method=method, client_host=self.addr)
		req_handler.handle_connection()
		# # # # #TODO: figure out code reuse strategy between here and WebRequestHandler
		# # # # def recv_until(terminator=b'\r\n', recv_size=128, sock=sock, buf=buf):
		# # # # 	try:
		# # # # 		while not terminator in buf:
		# # # # 			recv_data = sock.recv(recv_size)
		# # # # 			buf = buf + recv_data
		# # # # 			if len(recv_data)==0:
		# # # # 				return None
		# # # # 	except socket.timeout:
		# # # # 		raise RequestTimedOut()
		# # # # 	(ret, rem) = buf.split(terminator, 1)
		# # # # 	buf = rem
		# # # # 	return ret+terminator
		# # # # def recv_bytes(num_bytes, sock=sock, buf=buf):
		# # # # 	try:
		# # # # 		while len(buf) < num_bytes:
		# # # # 			recv_size = num_bytes-len(buf)
		# # # # 			recv_data = sock.recv(recv_size)
		# # # # 			buf = buf + recv_data
		# # # # 			if len(recv_data)==0:
		# # # # 				buf = b''
		# # # # 				return buf
		# # # # 	except socket.timeout:
		# # # # 		raise RequestTimedOut()
		# # # # 	ret = buf[:num_bytes]
		# # # # 	buf = buf[num_bytes:]
		# # # # 	return ret
		# # # # def parse_headers(headers):
		# # # # 	return dict([tuple(l.split(': ',1)) for l in headers.split('\r\n') if ': ' in l])
		


		# # # # request_str = '{method} {resource} HTTP/1.1\r\nHost: {host}\r\n'.format(resource=resource, method=method, host=self.addr)
		# # # # if body is None:
		# # # # 	request_str = request_str+'\r\n'
		# # # # 	request_dat = request_str.encode('utf-8')
		# # # # else:
		# # # # 	request_str = request_str+'Content-Length: {length}\r\n'.format(length=len(body))
		# # # # 	request_str = request_str+'\r\n'
		# # # # 	request_dat = request_str.encode('utf-8')
		# # # # 	request_dat = request_dat + body
		# # # # sock.write(request_dat)
		# # # # status = recv_until()
		# # # # headers_dat = recv_until('\r\n\r\n')
		# # # # headers = parse_headers(headers_dat)
		# # # # #TODO: get content length and receive data, just like in WebRequestHandler.recv_request
		# # # # # TODO: maybe instead use WebRequestHandler, and modify to have a 'client' mode for parsing
		
