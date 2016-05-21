"""
This class keeps track of the test machines connected to the Selenium Grid system.
"""

import ConfigParser
import json
import re
import urllib2
from os import path, environ
import socket

from objects.test_machine_obj import TestMachineObj

import django
from sys import path as syspath


environ['PYTHONPATH'] = path.abspath(path.join(syspath[0], '..', '..'))
environ['DJANGO_SETTINGS_MODULE'] = 'dashboard.settings'

django.setup()

from testautomation.models import TestMachine


class TestMachineManager:
    def __init__(self, project_path):
        self._base_url = 'http://%s:%s/grid/api/proxy?id=' % (socket.gethostname(), self.get_port(project_path))

        for model in TestMachine.objects.all():
            model.url = None
            model.uuid = None
            model.active = False
            model.save()

    @staticmethod
    def get_port(project_path):
        """
        This method retrieves port number from the configuration file.
        """

        config = ConfigParser.ConfigParser()
        config_path = path.abspath(path.join(project_path, 'config.ini'))
        config.read(config_path)
        return config.get('SELENIUMSERVER', 'hub_port')

    def get_machines(self):
        """
        This method checks which of the machines in the machine list are active (in case one or more machines have,
        disconnected, but Selenium Standalone Server has not yet been notified), and returns the list of the active
        machines.
        """

        tmp_machines = [machine for machine in TestMachine.objects.filter(approved=True) if self.is_active(machine)]

        machines = []
        for machine in tmp_machines:
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

    @staticmethod
    def is_active(machine):
        """
        This method checks whether a test machine is connected and active by checking the error code from the URL of the
        test machine, which should return '403' if the machine is connected and active.
        """

        active = False
        try:
            urllib2.urlopen(machine.url)
        except urllib2.HTTPError, e:
            active = True if e.code == 403 else False
        except:
            pass
        if not active:
            machine.active = False
            machine.save()
        return active

    def add_machine(self, url):
        """
        This method checks if a test machine discovered by Selenium Standalone Server has the required configuration
        details needed by OptiRun. If it does, a 'TestMachineObj" is created and added to the list of active test
        machines. Otherwise, the connection is ignored.
        """

        json_url = self._base_url+url
        while True:
            try:
                response = urllib2.urlopen(json_url)
                data = json.loads(response.read())

                if data['success'] and not data['request']['configuration']['uuid']:
                    break
                if len(data['request']['capabilities']) >= 1:
                    platform = self.get_platform(data['request']['capabilities'][0]['platform'])
                else:
                    break

                model = TestMachine.objects.filter(
                    hostname__iexact=data['request']['configuration']['hostname']
                ).first()
                if not model:
                    model = TestMachine(
                        hostname=data['request']['configuration']['hostname'],
                        approved=False
                    )
                self.add_model(model, data, platform)
                print "New test machine connected: %s" % url
                break
            except:
                continue

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
