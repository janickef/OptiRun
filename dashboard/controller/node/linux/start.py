import os
import re
import sys
import urllib2
import uuid
from subprocess import Popen, PIPE
import ConfigParser

import socket


def get_version(browser):
	try:
		out = Popen([browser, '--version'], stdout=PIPE, stderr=PIPE).stdout.read()
		return re.sub(r'([a-zA-Z \n])', "", out)
	except:
		return None

def get_selenium_settings():
    config = ConfigParser.ConfigParser()
    config.read(os.path.abspath(os.path.join(sys.path[0], 'config.ini')))
    port = config.get('CONFIG', 'port')
    hub_host = config.get('CONFIG', 'hub_host')

    try:
        socket.inet_aton(socket.gethostbyname(hub_host))
        return port, hub_host
    except socket.error:
        return port, config.get('CONFIG', 'hub_ip')

def get_selenium_path():
	"""
	This method locates the Selenium Standalone Server and returns its location and filename if it exists. Otherwise, it
	downloads the file from a URL.
	"""

	for f in os.listdir(sys.path[0]):
		if f.startswith('selenium-server-standalone') and f.endswith('.jar'):
			return os.path.abspath(os.path.join(sys.path[0], str(f)))
	try:
		print "Could not find Selenium Standalone Server. Attempting to download..."
		response = urllib2.urlopen(
			"https://selenium-release.storage.googleapis.com/2.51/selenium-server-standalone-2.51.0.jar")
		CHUNK = 16 * 1024
		with open(os.path.abspath(os.path.join(sys.path[0], 'selenium-server-standalone-2.51.0.jar')), 'wb') as f:
			while True:
				chunk = response.read(CHUNK)
				if not chunk:
					break
				f.write(chunk)
		print "Finished downloading Selenium Standalone Server."
		return os.path.abspath(os.path.join(sys.path[0], 'selenium-server-standalone-2.51.0.jar'))
	except:
		print "Something went wrong while attempting to download Selenium Standalone Server. Exiting..."


if __name__ == "__main__":
	uu_id = str(uuid.uuid1())

	port, hub_host = get_selenium_settings()

	command = [
		'java', '-jar', '"%s"' % get_selenium_path(),
		'-role', 'webdriver',
		'-hostname', '"%s"' % socket.gethostname(),
		'-hubHost', hub_host,
		'-port', port,
		'-uuid', uu_id,
	]

	firefox_ver = get_version('firefox')
	print firefox_ver
	if firefox_ver:
		command += [
			'-browser',
			'"browserName=%s,version=%s,applicationName=%s"' % ('firefox', firefox_ver, uu_id)
		 ]

	chrome_ver = get_version('google-chrome')
	print chrome_ver
	if chrome_ver:
		command += [
			'-browser',
			'"browserName=%s,version=%s,applicationName=%s"' % ('chrome', chrome_ver, uu_id),
			'-Dwebdriver.chrome.driver="%s"' % os.path.abspath(os.path.join(sys.path[0], 'drivers', 'chromedriver'))
		]

	p = Popen(" ".join(command), stderr=PIPE, shell=True)

	with p.stderr:
		for line in iter(p.stderr.readline, b''):
			print line.replace('\n', '')
