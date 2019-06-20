#! /usr/bin/env python

from .WebDocs import WebDocs
from .WebFileInterface import WebFileInterface
from .WebDispatcher import WebDispatcher
from .ConnDispatcher import ConnDispatcher
from .misc import init_logger, set_loglevel, addr_rep

class WebHost(object):
	'''
		class for hosting a "/static" folder
		allows WebInterface objects to serve dynamic content alongside the "/static" folder
	'''
	def __init__(self,timeout=10,loglevel='INFO',staticdir="static",staticindex="index.html",include_fp=['{staticdir}/*'],exclude_fp=[], error_404_page_func=None):
		set_loglevel(loglevel)
		self.log_handler = init_logger(__name__)
		self.addr=[]
		self.web_dispatcher = WebDispatcher(addr=self.addr, timeout=timeout, error_404_page_func=error_404_page_func)
		self.dispatcher = ConnDispatcher()
		self.docs = WebDocs(self)
		self.docs.connect_funcs()
		self.web_file_interface = WebFileInterface(host=self, addr=self.addr, staticdir=staticdir, staticindex=staticindex,include_fp=include_fp,exclude_fp=exclude_fp)

	def add_addr(self, addr=None, port=80, TLS=None):
		'''
		adds an address to the dispatcher for it to listen on
		addr should be a hostname to listen on, or None to listen on all addresses
		port should be a port number to listen on
		TLS should be a tuple of two filenames to use for the certfile and keyfile for TLS, or None to use plain HTTP
		'''
		addr_tuple = ((addr,port),TLS)
		self.addr.append(addr_tuple)
		self.dispatcher.add_conn_listener(addr_tuple, self.web_dispatcher.handle_connection, name='WebDispatch_'+addr_rep(addr_tuple))

	def start_service(self):
		if len(self.addr)==0:
			self.log_handler.warn('No port number specified! Defaulting to port 80!')
			self.add_addr()
		self.log_handler.info('Starting web server on {addr}'.format(addr=addr_rep(self.addr)))
		self.log_handler.debug("All Resources: {}".format(self.get_docs().GET_DOCS_JSON()))
		self.dispatcher.start_service()
	
	def stop_service(self):
		self.log_handler.info('Stopping web server on {addr}'.format(addr=addr_rep(self.addr)))
		self.dispatcher.stop_service()
		self.log_handler.info('Web server stopped on {addr}'.format(addr=addr_rep(self.addr)))

	def get_dispatcher(self):
		return self.dispatcher

	def get_web_dispatcher(self):
		return self.web_dispatcher

	def get_docs(self):
		return self.docs
