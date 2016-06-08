"""
This class maintains the execution queues, handles test executions and reports the results to the database.
"""

import ConfigParser
import json
import os
import socket
import sys
import threading
import time
from multiprocessing import Lock
from subprocess import Popen, PIPE

from optix import OptiX

import django
from django.utils import timezone

project_path = os.path.abspath(os.path.join(sys.path[0], '..', '..'))

if project_path not in sys.path:
    sys.path.append(project_path)

os.environ['PYTHONPATH'] = os.path.abspath(os.path.join(sys.path[0], '..', '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'dashboard.settings'

django.setup()

from testautomation.models import Log

class Executor:
    def __init__(self, test_machine_manager):
        self._test_machine_manager = test_machine_manager
        self._optix = OptiX()

        self._q1 = []  # Queue 1 - Highest priority queue for immediate test execution requests
        self._q2 = []  # Queue 2 - Queue for planned test executions
        self._executing_machines = []  # List of UUIDs of machines currently executing tests

        self._queue_lock = Lock()  # Lock which must be acquired to add to or empty queues
        self._execution_lock = Lock()  # Lock which must be acquired to add to or empty queues

        self._hub_port, self._script_path = self.get_config_settings()

        ql = threading.Thread(target=self.queue_listener)
        ql.start()

    @staticmethod
    def get_config_settings():
        """
        This method retrieves the hub port number and the base path of test scripts within the project from the
        configuration file.
        """

        config = ConfigParser.ConfigParser()
        config_path = os.path.abspath(os.path.join(sys.path[0], '..', '..', 'config.ini'))
        config.read(config_path)

        hub_port = config.get('SELENIUMSERVER', 'hub_port')
        script_path = config.get('CONTROLLER', 'script_basepath')

        return hub_port, script_path

    def queue_listener(self):
        """
        This method continuously checks the queues. If there are tests in Queue 1, they are forwarded for execution. To
        avoid starvation, any tests in Queue 2 are then moved to Queue 1. If there are tests in Queue 2 and Queue 1 is
        empty, the tests in Queue 2 are forwarded for execution. In order to forward tests for execution, the execution
        lock must first be acquired.
        """

        while True:
            if self._q1 and self._execution_lock.acquire(False):
                self._queue_lock.acquire()
                print "Handling tests from Queue 1"
                self.handle_tests(self._q1)
                self._q1 = []
                if self._q2:
                    self._q1 = self._q2
                    self._q2 = []
                self._queue_lock.release()
            elif self._q2 and not self._q1 and self._execution_lock.acquire(False):
                self._queue_lock.acquire()
                print "Handling tests from Queue 2"
                self.handle_tests(self._q2)
                self._q2 = []
                self._queue_lock.release()

    def add_to_q1(self, tests):
        """
        This method takes a list of tests and adds each test to Queue 1 if there is not an identical test currently
        placed in Queue 1. It then removes any duplicates from Queue 2.
        """

        self._queue_lock.acquire()
        self._q1 += [t for t in tests if t not in self._q1]
        self._q2 = [t for t in self._q2 if t not in self._q1]
        self.print_update()
        self._queue_lock.release()

    def add_to_q2(self, tests):
        """
        This method takes a list of tests and adds each test to Queue 2 if there is not an identical test currently
        placed in either Queue 1 or Queue 2.
        """

        self._queue_lock.acquire()
        self._q2 += [t for t in tests if t not in self._q2 and t not in self._q1]
        self.print_update()
        self._queue_lock.release()

    def print_update(self):
        """
        This method is used to print queue updates.
        """
        print "*** UPDATED QUEUES ***"
        self.print_queue("Queue 1:", self._q1)
        self.print_queue("Queue 2:", self._q2)

    @staticmethod
    def print_queue(queue_str, queue):
        """
        This methjod prints the queue.
        """

        print queue_str
        if queue:
            for test in queue:
                print test
        else:
            print "<Empty>"

    def handle_tests(self, tests):
        """
        This method uses an instance of 'OptiX' to allocate tests to test machines. It calls the 'report_results' method
        to report any non-executable tests. If no tests are executable, the execution lock is released, and the method
        returns. Otherwise, it starts the 'run_test_set' method for each machine in separate threads.
        """

        non_executables, allocations = self._optix.allocate(self._test_machine_manager.get_machines(), tests)

        if non_executables:
            t = timezone.now()
            for test in non_executables:
                note = "Not executed"
                self.report_results(test, t, t, note, None, None, None, None, None, None, None, None, None, None)

        if len(tests) == len(non_executables):
            self._execution_lock.release()
            return

        for allocation in allocations:
            threading.Thread(target=self.run_test_set, args=(allocation,)).start()

    def run_test_set(self, allocation):
        """
        This method takes a dictionary containing a test machine and a test set, and calls the 'execute' method for each
        test in the set one by one. After each execution, the method checks if the test machine is still live; if it is
        not, the tests that haven't successfully been executed is put back in Queue 1, and the method returns. If the
        test machine is still live after an execution, the result is reported to the database by calling the
        'report_results' method. When the method returns, it removes the machine's uuid from the list of executing,
        and releases the execution lock if the list is empty.
        """

        self._executing_machines.append(allocation['machine'].uuid)

        for i, test in enumerate(allocation['test_set']):
            start = time.clock()
            start_time = timezone.now()

            script_path = os.path.abspath(os.path.join(sys.path[0], '..', '..', self._script_path, test.script_name))
            result, test_duration, output, console_log = self.execute(test, script_path, allocation['machine'].uuid)

            if not self._test_machine_manager.is_active(allocation['machine']):
                self.add_to_q1(allocation['test_set'][i:])
                if allocation['machine'].uuid in self._executing_machines:
                    self._executing_machines.remove(allocation['machine'].uuid)
                    if not self._executing_machines:
                        self._execution_lock.release()
                return

            browser_ver = None
            for b in allocation['machine'].browsers:
                if test.browser.replace(" ", "-").lower() == b['browser'].replace(" ", "-").lower():
                    browser_ver = b['version']
                    break

            end_time = timezone.now()
            precise_duration = time.clock()-start

            self.report_results(
                test, start_time, end_time, None, result, test_duration, precise_duration,
                output, console_log, allocation['machine'].ip, test.browser, browser_ver,
                allocation['machine'].platform['os'], allocation['machine'].platform['version']
            )

        if allocation['machine'].uuid in self._executing_machines:
            self._executing_machines.remove(allocation['machine'].uuid)
        if not self._executing_machines:
            self._execution_lock.release()
            print "releasing execution lock..."

        print self._executing_machines, self._execution_lock, "returning"

    def execute(self, test, script_path, app_name):
        """
        This method builds a command that executes the test as a subprocess, which Selenium Grid then sends to one of
        the test machines depending on the specifications defined in the 'desired_capabilities' dictionary. All
        The specifications are packed as a JSON string and added to the command, and is unpacked in the test script if
        the script follows the template for OptiRun test scripts. This method also listens to and interprets the output,
        and returns the results of the test execution accordingly.
        """

        command_executor = 'http://%s:%s/wd/hub' % (socket.gethostname(), self._hub_port)

        desired_capabilities = {
            'browserName'    : test.browser,
            'applicationName': app_name
        }

        data = {
            'command_executor'    : command_executor,
            'desired_capabilities': desired_capabilities
        }

        json_data = json.dumps(data)
        start = time.clock()

        #script_path.replace('\f', '\\f')
        p = Popen(['python', script_path, json_data], shell=True, stderr=PIPE, stdout=PIPE)
        output, error = p.communicate()

        print "ERROR:", error
        print "OUTPUT:", output

        try:
            result = error.splitlines()[-3]
            duration = float(result.split()[-1].replace("s", ""))

            if "ok" in error.splitlines()[-1].lower():
                result = True
                print "PASSED: '%s'" % test.title
            else:
                result = False
                print "FAILED: '%s'" % test.title
        except:
            result = False
            print "Something went wrong when trying to execute '%s'" % test.title
            duration = time.clock()-start

        return result, duration, output, error

    @staticmethod
    def report_results(test, start_time, end_time, note, result, duration, total_duration,
                       output, console_log, ip, browser, browser_ver, platform, platform_ver):
        """
        This method creates a new 'Log' instance and saves it to the database using Django's database API
        """

        l = Log(
            test=test.title,
            script_name=test.script_name,
            start_time=start_time,
            end_time=end_time,
            result=result,
            test_duration=duration,
            total_duration=total_duration,
            note=note,
            output=output,
            console_log=console_log,
            test_machine_ip=ip,
            browser=browser,
            browser_ver=browser_ver,
            platform=platform,
            platform_ver=platform_ver,
            test_id=test.id,
        )
        l.save()

