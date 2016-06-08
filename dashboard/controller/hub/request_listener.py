"""
This class listens for test execution requests triggered from the dashboard.
"""

import ConfigParser
import json
import os
import socket
import sys

from objects.test_obj import TestObj


class RequestListener:

    def __init__(self):
        self._port, self._buffer_size = self.get_config_settings()

    @staticmethod
    def get_config_settings():
        """
        This method retrieves port number and buffer size from the configuration file.
        """

        config = ConfigParser.ConfigParser()
        config_path = os.path.abspath(os.path.join(sys.path[0], '..\..', 'config.ini'))
        config.read(config_path)

        port = config.get('CONTROLLER', 'request_port')
        buffer_size = config.get('CONTROLLER', 'buffer_size')

        return int(port), int(buffer_size)

    def listen_for_requests(self, test_executor):
        """
        This method continuously listens for test execution requests triggered from the dashboard.
        """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((socket.gethostname(), self._port))
        s.listen(1)

        while True:
            conn, addr = s.accept()
            while True:
                json_data = conn.recv(self._buffer_size)
                if json_data:
                    try:
                        tests = []
                        data = json.loads(json_data)
                        for obj in data:
                            tests.append(TestObj(
                                obj['pk'],
                                obj['title'],
                                obj['script'],
                                obj['avg_duration'],
                                str(obj['browser']),
                                str(obj['platform']),
                            ))
                        test_executor.add_to_q1(tests)
                    except:
                        pass
                else:
                    break
            conn.close()
