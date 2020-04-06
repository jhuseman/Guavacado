# Guavacado changelog
made by Joshua Huseman, jhuseman@alumni.nd.edu

## 0.1.0 (06/08/2016)
## 0.2.0 (06/13/2016)
## 0.3.0 (08/01/2017)
- removed logging to screen
## 1.0.0 (06/16/2018)
- removed `cherrypy` dependency, instead using python built-in `BaseHTTPServer`
## 1.0.1 (02/08/2019)
- added check in "`connect`" function to operate just like "`connect_callback`" with function argument, added optional argument to WebInterface to specify host or host arguments
## 1.0.2 (02/13/2019)
- added request on "`stop_service`" function to force server to finish run loop
## 1.0.3 (02/13/2019)
- CRITICAL UPDATE: fixed bug allowing access to entire contents of drive upon opening url //
## 1.0.4 (02/14/2019)
- added `include_fp` and `exclude_fp` parameters to specify lists of directories or file patterns that can be accessed by the server
## 1.1.0 (02/22/2019)
- added full support for `python3`
## 1.1.1 (02/22/2019)
- fixed bug showing strange backslash in redirect page on Windows
## 1.1.2 (02/22/2019)
- added functionality to support the body of data in the first argument of a callback
## 1.1.2 (03/10/2019)
- updated for standalone library, Guavacado rebrand
## 1.1.3 (05/13/2019)
- separated components into various different files
## 1.9.0 (05/27/2019)
- started development branch [potential 2.0 release] for migration to raw sockets instead of `http_server`
- reformatted documentation into new locations, updated some out-of-date documentation
## 1.9.1 (05/27/2019)
- Moved `WebDispatcher` and `WebRequestHandler` to separate files
- Implemented `ConnListener` to listen for new socket connections
- Removed unnecessary imports in many files
## 1.9.2 (05/28/2019)
- Implemented full functionality on raw sockets
- Created `ConnHandler` for handling the HTTP protocol on the received socket connections
- `WebRequestHandler` deprecated - replaced by raw socket functionality of `ConnListener` and `ConnHandler`
## 1.9.3 (05/30/2019)
- Renamed `ConnHandler` to `WebRequestHandler`
## 1.9.4 (05/30/2019)
- fixed `python2` functionality
- Added functionality to invoke module with "`python -m guavacado`" for a simple web server
## 1.9.5 (05/31/2019)
- tested access from external to the network
- cleaned up code
## 1.9.6 (06/01/2019)
- added functionality to host on multiple ports
- added TLS/HTTPS support (untested)
	- certificate file and key file should be specified alongside address for the HTTPS ports
- changed syntax of specifying listening address
	- WebHost now expects an address in the format `addr=[((host,port),None)]` for http and `addr=[((host,port),(certfile,keyfile))]` for https instead of old `host=host,port=port` syntax
## 1.9.7 (06/19/2019)
- refactored multi-port functionality to add `ConnDispatcher`, separated from functionality of `WebDispatcher`
	- `ConnDispatcher` creates `ConnListener` instances for specific addresses and dispatches connections to the correct `WebDispatcher` (or similar class) instance
		- This allows for other classes like `WebDispatcher` to be developed to serve specific ports differently
		- Example potential expansions:
			- Concurrently run bare socket connections on a secondary port
			- restrict one port to only serve files while another port serves a `WebInterface`
			- Redirect all traffic over a non-TLS socket to the HTTPS port number
		- These expansions should be accessible as an optional argument to the `WebHost.add_addr()` function in a later version
	- `WebDispatcher` passes a connection through `WebRequestHandler`, then dispatches the request to the correct `Webinterface` (or similar class) instance
		- `WebFileInterface` is a variation on the `WebInterface` class specifically for file hosting
- re-implemented file hosting functionality (missing in version 1.9.6) in `WebFileInterface` class
- changed syntax (again) of specifying listening address
	- addresses should now be specified by calling `WebHost.add_addr()` for each address after instantiating `WebHost`
## 1.9.8 (06/27/2019)
- implemented `RedirectDispatcher` class to redirect all traffic to a different protocol and domain name (primarily to redirect HTTP to HTTPS traffic)
- added `tls_keygen.sh` to create a self-signed certificate for a secure TLS connection
- added redirect from HTTP to HTTPS on the default setup created my `__main__.py`
- created `http_status_codes.py` taking data from [Wikipedia](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes) for a more complete list of string identifiers for HTTP status codes
- improved redirect page to send a HTTP redirect status code for faster redirection (instead of HTTP or JavaScript redirection)
## 1.9.9 (07/25/2019)
- implemented `RawSocketDispatcher` class to simply call a callback function on every connection with the socket instance
	- to implement this, call `WebHost.add_addr(port=999, disp_type=('raw_socket', callback))`
	- the callback function will be called with the arguments: `callback(socket, address, client_id)` to handle the connection
	- this could previously be done with a direct instantiation of the `ConnListener` class, but this change allows all interfaces to be accessed through the `WebHost`, `WebInterface`, and `WebFileInterface` classes
- added UDP (datagram) functionality
	- to use UDP, use the `UDP=True` argument to `WebHost.add_addr()`
	- this will not work properly with the default `'web'` `disp_type`, as it does not permit multiple discrete connections. Instead, use the `'raw_socket'` `disp_type`.
- added optional argument to `WebDispatcher` setup function inside of `WebHost`, allowing a special identifier to be specified when adding the address to isolate multiple `WebInterfaces` from one another
	- This can be done with the following code:
		```python
		host = WebHost()
		host.add_addr(port=80, disp_type=('web', 'web_80'))
		interface_80 = WebInterface(host=host, web_dispatcher_ident='web_80')
		host.add_addr(port=88, disp_type=('web', 'web_88'))
		interface_88 = WebInterface(host=host, web_dispatcher_ident='web_88')
		```
	- After running this code, requests to port 80 would be served by `interface_80`, while requests to port 88 would be served by `interface_88`
- removed automatic instantiation of `WebFileInterface` in `WebHost`.  Now requires explicit instantiation of `WebFileInterface` to serve files (allows REST APIs without file hosting)
- implemented HEAD request functionality in `WebFileInterface`
- cleaned up `__init__.py` to remove unnecessary public API components that have no use as parts of the public API
- modified `WebDocs` class to use a discrete instance of `WebInterface`, instead of using inheritance - following my own guidelines
- added `Client` class for connection to a guavacado server, or any other web server
- added test cases to test proper functionality of client and server
## 1.9.10 (04/06/2019)
- implemented HTTP Basic authentication
	- This is implemented via the `add_addr` function and a new `BasicAuth` class, using the following code:
		```python
		host = WebHost()
		auth = BasicAuth(auth_dict={
			'username' :'password',
			'username2':'password2'
			}, realm='Password-protected server')
		host.add_addr(port=80, disp_type=('web', 'password_protected', auth))
		interface = WebInterface(host=host, web_dispatcher_ident='password_protected')
		```
	- An alternate implementation using `BasicAuth` allows a function to determine the validity of the credentials, instead of the `auth_dict` specified in the above code snippet.  This can be specified as follows:
		```python
		host = WebHost()
		def auth_handler(username, password):
			if username=='username' and password='password':
				return True
			if username=='username2' and password='password2':
				return True
			return False
		auth = BasicAuth(auth_handler=auth_handler, realm='Password-protected server')
		host.add_addr(port=80, disp_type=('web', 'password_protected', auth))
		interface = WebInterface(host=host, web_dispatcher_ident='password_protected')
		```

# TODO
- test TLS/HTTPS with public server
- add icon to docs or directory listing page (and maybe 404/500?)
- clean up imports on recently changed files
- update docstring on recently changed files
- change implementation of logging to use a log environment class, instead of global variables
- add command-line arguments to `__main__.py` to allow specification of what to run by default

- add functionality to Client to wrap a REST API into a single class (where member function calls make a request and return the body of the request)
- add class name of resources to docs pages for the REST API and allow client wrapper class to restrict connection to a single class
- allow exposing an entire class as a REST API with a single function call (ignoring "private" methods starting with an underscore)
