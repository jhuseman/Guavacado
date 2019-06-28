from .WebHost import WebHost
from .misc import wait_for_keyboardinterrupt
import os

def main():
	"""serves only a static folder in the local 'static' directory"""
	host = WebHost(loglevel='INFO')
	host.add_addr(port=80, disp_type=('redirect', 'https://localhost/'))
	host.add_addr(port=443, TLS=(os.path.join('TLS_keys','self_signed.crt'),os.path.join('TLS_keys','self_signed.key')))
	host.start_service()
	wait_for_keyboardinterrupt()
	host.stop_service()

if __name__ == '__main__':
	main()
