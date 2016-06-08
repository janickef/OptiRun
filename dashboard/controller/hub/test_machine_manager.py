"""
This class keeps track of the test machines connected to the Selenium Grid system.
"""

import ConfigParser
import json
import re
import socket
import urllib2

import os
import sys

import django
from bs4 import BeautifulSoup

from objects.test_machine_obj import TestMachineObj

project_path = os.path.abspath(os.path.join(sys.path[0], '..', '..'))

if project_path not in sys.path:
    sys.path.append(project_path)

os.environ['PYTHONPATH'] = os.path.abspath(os.path.join(sys.path[0], '..', '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'dashboard.settings'

django.setup()

from testautomation.models import TestMachine


class TestMachineManager:
    def __init__(self, project_path):
        self._base_url = 'http://%s:%s/grid/api/proxy?id=' % (socket.gethostname(), self.get_port(project_path))
        self._project_path = project_path
        self._hub_port = self.get_selenium_hub_port()

        for model in TestMachine.objects.all():
            model.url = None
            model.uuid = None
            model.active = False
            model.save()

    def get_selenium_hub_port(self):
        """
        This method retrieves the hub port number from the configuration file.
        """

        config = ConfigParser.ConfigParser()

        config_path = os.path.abspath(os.path.join(self._project_path, 'config.ini'))
        config.read(config_path)

        port = config.get('SELENIUMSERVER', 'hub_port')
        return port

    @staticmethod
    def get_port(project_path):
        """
        This method retrieves port number from the configuration file.
        """

        config = ConfigParser.ConfigParser()
        config_path = os.path.abspath(os.path.join(project_path, 'config.ini'))
        config.read(config_path)
        return config.get('SELENIUMSERVER', 'hub_port')

    def get_machines(self):
        """
        This method checks which of the machines in the machine list are active (in case one or more machines have,
        disconnected, but Selenium Standalone Server has not yet been notified), and returns the list of the active
        machines.
        """

        active_machines = self.get_active_machines()
        approved_machines = [machine for machine in TestMachine.objects.filter(approved=True) if machine.url in active_machines]

        machines = []
        for machine in approved_machines:
            browsers = []
            if machine.chrome:
                browsers.append({
                    'browser': 'chrome',
                    'version': machine.chrome,
                })
            if machine.internet_explorer:
                browsers.append({
                    'browser': 'internet explorer',
                    'version': machine.internet_explorer,
                })
            if machine.firefox:
                browsers.append({
                    'browser': 'firefox',
                    'version': machine.firefox,
                })
            if machine.edge:
                browsers.append({
                    'browser': 'edge',
                    'version': machine.edge,
                })

            platform = {
                'os': machine.operating_system,
                'version': machine.operating_system_ver
            }

            machines.append(TestMachineObj(
                browsers,
                machine.ip,
                platform,
                machine.url,
                machine.uuid,
            ))

        return machines

    def is_active(self, machine):
        """
        This method checks whether a test machine is connected and active by calling 'get_active_machines' to get a list
        of currently active machines connected to the hub, and checking if the specific machine is in the list.
        """

        if machine.url in self.get_active_machines():
            return True
        return False

    def get_active_machines(self):
        """
        This method checks the response from 'http://<HubHost>:4444/grid/console#', and extracts necessary information
        from the HTML code. The method creates a list of currently connected machines.
        """

        active_machines = []
        grid_url = 'http://%s:%s/grid/console#' % (socket.gethostname(), self._hub_port)
        try:
            soup = BeautifulSoup(urllib2.urlopen(grid_url).read(), "html.parser")
            for proxy in soup.findAll('div', attrs={'class': 'proxy'}):
                proxyname = proxy.find('p', attrs={'class': 'proxyname'}).text
                proxy_url = re.findall('http://(?:[0-9]|[$-_@.&+])+', proxyname)[0].replace(",", "")
                if 'connection refused' not in proxyname.lower():
                    active_machines.append(proxy_url)
        finally:
            return active_machines

    def add_machine(self, url):
        """
        This method checks if a test machine discovered by Selenium Standalone Server has the required configuration
        details needed by OptiRun. If it does, a 'TestMachineObj" is created and added to the list of active test
        machines. Otherwise, the connection is ignored.
        """

        print url

        json_url = self._base_url+url
        while True:
            #try:
            print 1
            response = urllib2.urlopen(json_url)
            print 2
            data = json.loads(response.read())
            print 3
            print json_url
            print 4
            if data['success'] and not data['request']['configuration']['uuid']:
                print 5
                print "breaking... 1"
                break
            if len(data['request']['capabilities']) >= 1:
                print 6
                platform = self.get_platform(data['request']['capabilities'][0]['platform'])
            else:
                print 7
                print "breaking... 2"
                break

            print 8
            if data['request']['configuration']['hostname']:
                models = TestMachine.objects.filter(
                    hostname__iexact=data['request']['configuration']['hostname']
                )
            else:
                print "breaking...3"
                break

            if models:
                model = models[0]
            else:
                print 10
                model = TestMachine(
                    hostname=data['request']['configuration']['hostname'],
                    approved=False
                )
            print 11
            self.add_model(model, data, platform)
            print 12
            print model
            print "New test machine connected: %s" % url
            break
            #except:
            #    continue
        print "goodbye"

    @staticmethod
    def add_model(model, data, platform):
        model.ip = data['request']['configuration']['host']
        model.url = data['request']['configuration']['url']
        model.uuid = data['request']['configuration']['uuid']
        model.active = True
        model.operating_system = platform['os']
        model.operating_system_ver = platform['version']

        for c in data['request']['capabilities']:
            if 'chrome' in c['browserName']:
                if 'version' in c:
                    model.chrome = c['version']
                else:
                    model.chrome = True
            elif 'firefox' in c['browserName']:
                if 'version' in c:
                    model.firefox = c['version']
                else:
                    model.firefox = True
            elif 'internet explorer' in c['browserName']:
                if 'version' in c:
                    model.internet_explorer = c['version']
                else:
                    model.internet_explorer = True
            if 'edge' in c['browserName']:
                if 'version' in c:
                    model.edge = c['version']
                else:
                    model.edge = True
        model.save()

    @staticmethod
    def deactivate_model(model):
        model.url = None
        model.uuid = None
        model.active = False
        model.save()

    @staticmethod
    def get_platform(init):
        """
        This method interprets the platform of a test machine and returns it in the right format.
        """

        platform = {}
        tmp = re.sub(r'([a-zA-Z])([0-9.])', r'\1 \2', re.sub(r'([,_;:-])', '.', init))

        split = tmp.split(" ")
        if len(split) > 1 and split[0].lower().startswith("win"):
            platform['os'] = "Windows"
            platform['version'] = split[1]
        elif tmp == "VISTA":
            platform['os'] = "Windows"
            platform['version'] = "Vista"
        else:
            platform['os'] = tmp.title()
            platform['version'] = None
        return platform

    def remove_machine(self, url):
        """
        This method removes a machine from the machine list.
        """

        model = TestMachine.objects.filter(url=url).first()
        if model:
            self.deactivate_model(model)
        print "Removed test machine: %s" % url

    def handle_hub_msg(self, msg):
        """
        This method handles all incoming messages from the hub to identify whether a test machine has connected or
        disconnected, and acts accordingly.
        """

        try:
            url = re.findall('http://(?:[0-9]|[$-_@.&+])+', msg)[0]
            if "registered a node" in msg.lower():
                self.add_machine(url)
            elif "cannot reach the node" in msg.lower():
                self.remove_machine(url)
        except:
            pass
