#! /usr/bin/env python

# ConnListener.py
# defines:
#	ConnListener
#
# made by Joshua Huseman, jhuseman@alumni.nd.edu

import socket
import threading
import logging

class ConnListener(object):
	'''
	opens a socket listening for a connection from a client
	calls conn_callback in a new thread with a socket when a connection is established
	'''
	def __init__(self, conn_callback, port=80, host=None, log_handler=logging.getLogger(__name__)):
		self.conn_callback = conn_callback
		self.port = port
		self.host = host
		if self.host is None:
			# get a local hostname for the computer
			self.host = socket.gethostname()
		self.log_handler = log_handler
		self.active_client_ids = []
		self.client_ids_lock = threading.Lock()
		self.client_info = {}
		self.stop_event = threading.Event()
		self.create_server_socket()
	
	def create_server_socket(self):
		'''creates a socket object listening for connections and saves it to the variable self.sock'''
		#TODO: add an option to create a TLS socket instead, to implement HTTPS - https://docs.python.org/3/library/ssl.html
		self.log_handler.debug('Starting listening on {host} port {port} for connections.'.format(host=self.host, port=self.port))
		# create an INET, STREAMing (TCP) socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# bind the socket to a public host, and a well-known port
		self.sock.bind((self.host, self.port))
		# become a server socket
		self.sock.listen(5) # 5 is the number of queued connections to allow before refusing connections from new clients - 5 is typically the maximum for the OS

	def gen_client_id(self):
		'''generate an id number to identify a client'''
		with self.client_ids_lock:
			if len(self.active_client_ids)==0:
				ret = 0
			else:
				lv = min(self.active_client_ids)
				uv = max(self.active_client_ids)
				if lv<=0:
					ret = uv+1
				else:
					ret = lv-1
			self.active_client_ids.append(ret)
		return ret

	def free_client_id(self, client_id):
		'''remove a specified client id from the list of active ids so it can be used again'''
		with self.client_ids_lock:
			if client_id in self.active_client_ids:
				self.active_client_ids.remove(client_id)

	def spawn_client_thread(self, clientsocket, address):
		'''
		spawn a thread to handle the client socket
		keep track of the client thread and socket in a dictionary to be used for shutdown
		'''
		client_id = self.gen_client_id()
		self.log_handler.info('Connection established from address {addr} [id {id}]'.format(addr=address,id=client_id))
		client_thread = threading.Thread(
			target=self.handle_client, 
			args=(clientsocket, address, client_id), 
			name='clienthandler_{}'.format(client_id), 
			daemon=True,
		)
		self.client_info[client_id] = {
			'socket':clientsocket,
			'address':address,
			'thread':client_thread,
		}
		client_thread.start()
		self.log_handler.debug('Thread number {ident} started for connection id {id}'.format(ident=client_thread.ident,id=client_id))
	
	def handle_client(self, clientsocket, address, client_id):
		'''
		handle the connection to the client
		should be running in separate thread
		'''
		self.conn_callback(clientsocket)
		self.log_handler.debug('Shutting down connection from address {addr} [id {id}]'.format(addr=address,id=client_id))
		clientsocket.shutdown(socket.SHUT_RDWR)
		self.log_handler.debug('CLosing connection from address {addr} [id {id}]'.format(addr=address,id=client_id))
		clientsocket.close()
		self.log_handler.debug('Closed connection from address {addr} [id {id}]'.format(addr=address,id=client_id))
		# remove references to this client before closing the thread
		if client_id in self.client_info:
			del self.client_info[client_id]
		self.free_client_id(client_id)

	def run(self):
		'''accept connections from clients and spawn threads for them'''
		while not self.stop_event.is_set():
			# accept connections from outside
			(clientsocket, address) = self.sock.accept()
			# spawn thread using the new socket
			self.spawn_client_thread(clientsocket, address)
	
	def stop(self):
		'''stop accepting connections and shut down all sockets'''
		self.log_handler.info('Stopping server socket.')
		self.stop_event.set()
		self.sock.shutdown(socket.SHUT_RDWR)
		self.sock.close()
		self.log_handler.info('Stopping client socket connections.')
		client_ids = self.client_info.keys()
		for client_id in client_ids:
			if client_id in self.client_info:
				client_dat = self.client_info[client_id]
				self.log_handler.debug('Stopping connection from address {addr} [id {id}]'.format(addr=client_dat['address'],id=client_id))
				client_dat['socket'].shutdown(socket.SHUT_RDWR)
				client_dat['socket'].close()
				self.log_handler.debug('Waiting for thread id {ident} to close'.format(ident=client_dat['thread'].ident))
				client_dat['thread'].join()
		self.log_handler.info('All client socket connections stopped.')
