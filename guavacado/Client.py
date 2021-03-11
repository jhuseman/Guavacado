#! /usr/bin/env python

import socket
import ssl
import threading
from datetime import datetime

from .misc import addr_rep, init_logger
from .WebRequestHandler import WebRequestHandler
from .ClientCookieStore import ClientCookieStore, ClientCookie

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
	def request_url(url, method='GET', body=None, TLS_check_cert=True, include_response_headers=False, response_headers_as_lists=False, follow_redir=False, redir_persist_cookies=True, cookie_store=None, extra_headers={}):
		c, r = Client.from_url(url, TLS_check_cert=TLS_check_cert)
		return c.request_web(
			resource=r, 
			method=method, 
			body=body, 
			include_response_headers=include_response_headers, 
			response_headers_as_lists=response_headers_as_lists, 
			follow_redir=follow_redir, 
			redir_persist_cookies=redir_persist_cookies, 
			cookie_store=cookie_store, 
			extra_headers=extra_headers
		)
	
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
	
	def request_web(self, resource='/', method='GET', body=None, include_response_headers=False, response_headers_as_lists=False, follow_redir=False, redir_persist_cookies=True, cookie_store=None, extra_headers={}):
		'''makes a web request and returns the body of the response'''
		ret = []
		ret_event = threading.Event()
		def req_callback(body, code, headers, ret=ret, ret_event=ret_event, include_response_headers=include_response_headers):
			if include_response_headers:
				ret.append((body, code, headers))
			else:
				ret.append((body, code))
			ret_event.set()
		self.request_web_async(
			req_callback, 
			resource=resource, 
			method=method, 
			body=body, 
			include_response_headers=True, 
			response_headers_as_lists=response_headers_as_lists, 
			follow_redir=follow_redir, 
			redir_persist_cookies=redir_persist_cookies, 
			cookie_store=cookie_store, 
			extra_headers=extra_headers
		)
		ret_event.wait()
		return ret[0]

	def request_web_async(self, callback, resource='/', method='GET', body=None, include_response_headers=False, response_headers_as_lists=False, follow_redir=False, redir_persist_cookies=True, cookie_store=None, timeout=None, extra_headers={}):
		'''makes a web request using the raw socket and returns the body of the response'''
		sock = self.connect_socket()
		# buf = b''
		if follow_redir:
			def redir_callback(body, code, headers, callback=callback, cookie_store=cookie_store):
				if code in [301,302,307,308]:
					redir_url = headers['Location'][0]
					if redir_url.startswith('/'):
						c = Client(addr=self.addr, port=self.port, TLS=self.TLS, UDP=self.UDP, disp_type=self.disp_type, TLS_check_cert=self.TLS_check_cert)
						r=redir_url
					else:
						c, r = Client.from_url(redir_url, TLS_check_cert=self.TLS_check_cert)
					if redir_persist_cookies:
						if cookie_store is None:
							cookie_store = ClientCookieStore()
						if 'Set-Cookie' in headers:
							SetCookieHeaders = headers['Set-Cookie']
							for cookie_header in SetCookieHeaders:
								cookie_store.AddCookie(ClientCookie.from_header(cookie_header, self.addr, resource))
					c.request_web_async(
						callback,
						resource=r,
						method=method,
						body=body,
						include_response_headers=include_response_headers,
						response_headers_as_lists=response_headers_as_lists,
						follow_redir=follow_redir,
						redir_persist_cookies=redir_persist_cookies,
						cookie_store=cookie_store,
						timeout=timeout,
						extra_headers=extra_headers
					)
				else:
					if include_response_headers:
						if response_headers_as_lists:
							ret_headers = headers
						else:
							ret_headers = dict([(k,v[0]) for k, v in headers.items()])
						callback(body, code, ret_headers)
					else:
						callback(body, code)
			req_callback = redir_callback
			req_include_response_headers = True
			req_response_headers_as_lists = True
		else:
			req_callback = callback
			req_include_response_headers = include_response_headers
			req_response_headers_as_lists = response_headers_as_lists

		if cookie_store is not None:
			# do 2-level deep copy of extra_headers, converting strings into 1-element lists of strings - this generates a dictionary that we can modify without changing the original dictionary's contents
			req_extra_headers = dict([(k,{True:v,False:[v]}[isinstance(v,list)].copy()) for k,v in extra_headers.items()])
			if not 'Cookie' in req_extra_headers:
				req_extra_headers['Cookie'] = []
			req_extra_headers['Cookie'].append(
				ClientCookieStore.GetClientCookiesHeaderText(
					cookie_store.GetCookiesMatchingCriteria(
						Domain=self.addr, 
						Path=resource, 
						Expiration=datetime.now(), 
						Secure={True:True, False:None}[self.TLS is not None]
					)
				)
			)
		else:
			req_extra_headers = extra_headers

		req_handler = WebRequestHandler(
			sock, 
			(self.addr, self.port), 
			None, 
			req_callback, 
			timeout=timeout, 
			is_client=True, 
			client_resource=resource, 
			client_body=body, 
			client_method=method, 
			client_host=self.addr,
			client_include_response_headers=req_include_response_headers, 
			client_headers_as_lists=req_response_headers_as_lists, 
			add_headers=req_extra_headers
		)
		req_handler.handle_connection()
		
