import sys
import re
import subprocess

from os import path, listdir

import uuid

from subprocess import Popen, PIPE

global linux_browsers
global selenium_browsers
global driver_browsers

linux_browsers = [
	'firefox',
	'google-chrome',
	'opera',
	'internet-explorer',
	'edge',
	'safari',
]

selenium_browsers = [
	'firefox',
	'chrome',
	'opera',
	'internet-explorer',
	'edge',
	'safari',
]

driver_browsers = [
	'firefox',
	'chrome',
	'opera',
	'ie',
	'edge',
	'safari',
]

def get_version(browser):
	try:
		p = Popen([browser, '--version'], stdout=PIPE, stderr=PIPE)
		out = p.stdout.read()
		return re.sub(r'([a-zA-Z \n])', "", out)
	except:
		return None

def get_browsers(current_dir, uu_id):
	browsers = {}

	for browser in linux_browsers:
		version = get_version(browser)
		if version:
			browsers[browser] = version

	ret_str = ''

	for browser, version in browsers.iteritems():
		driver =  get_driver(current_dir, driver_browsers[linux_browsers.index(browser)])
		if driver:
			ret_str += ' -browser "browserName=%s,version=%s,applicationName=%s"' % (selenium_browsers[linux_browsers.index(browser)], version, uu_id)
			ret_str += driver
		elif browser == 'firefox':
			ret_str += ' -browser "browserName=%s,version=%s,applicationName=%s"' % (selenium_browsers[linux_browsers.index(browser)], version, uu_id)

	return ret_str

def get_selenium_server_path(current_dir):
	for file in listdir(current_dir):
		if file.startswith('selenium-server-standalone') and file.endswith('.jar'):
			return path.abspath(path.join(current_dir, str(file)))

def get_driver(current_dir, browser):
	driver_dir = path.abspath(path.join(current_dir, 'drivers'))
	for file in listdir(driver_dir):
		if browser in file:
			return ' -Dwebdriver.%s.driver=%s' % (browser, path.abspath(path.join(driver_dir, str(file))))

if 'linux' in sys.platform:
	uu_id = str(uuid.uuid1())
	current_dir = sys.path[0]

	selenium_server_path = get_selenium_server_path(current_dir)
	
	command = 'java -jar "%s"' % selenium_server_path
	command += ' -role node'
	command += ' -hubHost %s' % "lnor010710"
	command += ' -uuid %s' % uu_id
	command += get_browsers(current_dir, uu_id)

	output = path.abspath(path.join(current_dir, 'command.txt'))

	f = open(output, 'w')
	f.write(command)
	f.close()

	p = Popen([command], stderr=PIPE, shell=True)

	with p.stderr:
		for line in iter(p.stderr.readline, b''):
			print line.replace('\n', '')
