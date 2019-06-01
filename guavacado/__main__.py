import threading
import time

from .WebHost import WebHost

def wait_for_keyboardinterrupt():
	try:
		while True:
			time.sleep(86400) # wait 24 hours before looping again
	except KeyboardInterrupt:
		pass

def main():
	"""serves only a static folder in the local 'static' directory"""
	host = WebHost([
		((None,80),None),
		((None,81),None),
		((None,82),None),
		((None,83),None),
		# ((None,880),('test','test')),
	], loglevel='INFO')
	host.start_service()
	wait_for_keyboardinterrupt()
	host.stop_service()

if __name__ == '__main__':
	main()
