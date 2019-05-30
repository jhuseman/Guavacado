import threading
import time

from .WebHost import WebHost

def main():
	"""serves only a static folder in the local 'static' directory"""
	host = WebHost(80)
	threading.Thread(target=host.start_service).start()
	try:
		while True:
			time.sleep(1000)
	except KeyboardInterrupt:
		pass
	host.stop_service()

if __name__ == '__main__':
	main()
