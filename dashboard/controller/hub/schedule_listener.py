"""
This class retrieves and keeps track of the schedule, and forwards tests due for execution.
"""

import ConfigParser
import json
import os
import socket
import sys
import threading
import time
from datetime import datetime
from multiprocessing import Lock
from os import path

import django
from dateutil.rrule import rrulestr
from django.db.models import Avg

from objects.test_obj import TestObj

os.environ['PYTHONPATH'] = os.path.abspath(os.path.join(sys.path[0], '..', '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'dashboard.settings'

django.setup()

from testautomation.models import Schedule, Log


class ScheduleListener:
    def __init__(self, test_executor):
        self._executor = test_executor
        self._prev_time = datetime.utcnow()
        self._schedule = self.get_schedule()
        self._lock = Lock()

    def start_threads(self):
        threading.Thread(target=self.listen_for_updates).start()
        threading.Thread(target=self.check_schedule).start()
        threading.Thread(target=self.keep_schedule_updated).start()

    @staticmethod
    def get_schedule():
        """
        This method retrieves the schedule from the database, and adds the items that are scheduled in the future and
        marked as 'activated' to the schedule list.
        """
        data = Schedule.objects.filter(activated=True)

        schedules = {}
        for item in data:
            next_occurrence = rrulestr(item.rrule_string).after(datetime.utcnow())
            if next_occurrence:
                schedules[item.pk] = next_occurrence

        return schedules

    @staticmethod
    def get_config_settings():
        """
        This method retrieves port number and buffer size from the configuration file.
        """

        config = ConfigParser.ConfigParser()
        config_path = path.abspath(path.join(path.dirname(__file__), '..\..', 'config.ini'))
        config.read(config_path)

        port = config.get('CONTROLLER', 'schedule_port')
        buffer_size = config.get('CONTROLLER', 'buffer_size')

        return int(port), int(buffer_size)

    def listen_for_updates(self):
        """
        This method continuously listens for messages regarding added, updated or deleted 'Schedule' items, and updates
        the schedule list accordingly.
        """

        port, buffer_size = self.get_config_settings()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), port))
        s.listen(1)

        while True:
            conn, addr = s.accept()
            self._lock.acquire()
            while True:
                json_data = conn.recv(buffer_size)
                if json_data:
                    try:
                        data = json.loads(json_data)
                        for item in data:
                            next_occurrence = rrulestr(item['rrule_string']).after(datetime.utcnow())
                            if next_occurrence and item['activated']:
                                self._schedule[item['pk']] = next_occurrence
                                print "Added/updated %i" % item['pk']
                            else:
                                res = self._schedule.pop(item['pk'])
                                if res:
                                    print "Removed %i from schedule" % item['pk']
                    except:
                        pass
                else:
                    break
            self._lock.release()
            conn.close()

    def check_schedule(self):
        """
        This method is run as a thread, and continuously checks if there are any 'Schedule' items due now,
        and adds any tests belonging to the 'Schedule' items to Queue 2 for execution.
        """

        prev_time = datetime.utcnow()
        while True:
            new_time = datetime.utcnow()

            # Identifying if any 'Schedule' items are due now
            self._lock.acquire()
            tmp_schedules = [pk for pk, no in self._schedule.iteritems() if prev_time < no <= new_time]
            self._lock.release()

            if tmp_schedules:
                schedules = []
                for pk in tmp_schedules:
                    for obj in Schedule.objects.filter(pk=pk):
                        schedules.append(obj)
                tests = []
                for schedule in schedules:

                    # Retrieving any individual 'TestCase' items belonging to 'Schedule' items due now
                    tests = self.add_to_test_list(tests, schedule.test_cases.all())

                    # Retrieving any 'TestCase' items from 'Group' items belonging to 'Schedule' items due now
                    for group in schedule.groups.all():
                        tests = self.add_to_test_list(tests, group.test_cases.all())

                    next_occurrence = rrulestr(schedule.rrule_string).after(new_time)
                    self._lock.acquire()
                    if next_occurrence:
                        self._schedule[schedule.pk] = next_occurrence
                    else:
                        res = self._schedule.pop(schedule.pk, None)
                        if res:
                            print "Removed %i from schedule" % schedule.pk['pk']
                    self._lock.release()
                if tests:
                    self._executor.add_to_q2(tests)

            prev_time = new_time
            time.sleep(0.1)

    @staticmethod
    def add_to_test_list(test_list_1, test_list_2):
        """
        This method adds the tests that are in 'test_list_2', but not in 'test_list_1' to the latter list.
        """

        for test in test_list_2:
            if not any([test.pk == t.id for t in test_list_1]):
                test_list_1.append(TestObj(
                    test.pk,
                    test.title,
                    str(test.script),
                    Log.objects.filter(test_id=test.pk).exclude(result__isnull=True).aggregate(
                        Avg('test_duration'))['test_duration__avg'],
                    'any',
                    'any'
                ))
        return test_list_1

    def keep_schedule_updated(self):
        """
        This method discards the currently stored schedule and retrieves a new, updated schedule
        every 900 seconds (15 minutes)
        """

        while True:
            tmp_schedule = self.get_schedule()
            self._lock.acquire()
            self._schedule = tmp_schedule
            self._lock.release()
            time.sleep(900)

