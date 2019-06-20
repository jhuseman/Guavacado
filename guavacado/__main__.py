from .WebHost import WebHost
from .misc import wait_for_keyboardinterrupt

def main():
	"""serves only a static folder in the local 'static' directory"""
	host = WebHost(loglevel='INFO')
	host.add_addr(port=80)
	host.add_addr(port=81)
	host.add_addr(port=82)
	host.add_addr(port=83)
	# host.add_addr(port=880, TLS=('test','test'))
	host.start_service()
	wait_for_keyboardinterrupt()
	host.stop_service()

if __name__ == '__main__':
	main()
