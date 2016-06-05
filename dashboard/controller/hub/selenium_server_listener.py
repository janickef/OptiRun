"""
This class starts the Selenium Grid Hub and continuously listens to the output.
"""

import ConfigParser
from os import path, listdir
from subprocess import Popen, PIPE, CREATE_NEW_CONSOLE


class SeleniumHub:
    def __init__(self, project_path, controller_path, test_machine_manager):
        self._project_path = project_path
        self._controller_path = controller_path
        self._test_machine_manager = test_machine_manager

        self._port, self._node_timeout = self.get_selenium_settings()
        self._selenium_path = self.get_selenium_path()

    def get_selenium_settings(self):
        """
        This method retrieves the hub port number and the node timeout from the configuration file.
        """

        config = ConfigParser.ConfigParser()

        config_path = path.abspath(path.join(self._project_path, 'config.ini'))
        config.read(config_path)

        port = config.get('SELENIUMSERVER', 'hub_port')
        node_timeout = config.get('SELENIUMSERVER', 'node_timeout')

        return port, node_timeout

    def get_selenium_path(self):
        """
        This method locates the Selenium Standalone Server in the 'controller' directory and returns its location and
        file name (enables upgrading the Selenium Standalone Server without having to change the code).
        """

        for f in listdir(self._controller_path):
            if f.startswith("selenium-server"):
                return path.abspath(path.join(self._controller_path, str(f)))
        print "Could not find Selenium Standalone Server executable JAR..."
        exit()

    def start_selenium_grid(self):
        """
        This method builds the command needed to start the Selenium Grid Hub correctly, executes the command as a sub-
        process, and listens to the output. The output is handled by the 'handle_hub_msg' method of the test machine
        manager.
        """

        cmd = [
            'java',
            '-jar',
            self._selenium_path,
            '-port',
            self._port,
            '-role',
            'hub',
            '-nodeTimeout',
            self._node_timeout,
            #'-host 10.0.0.4'
        ]

        p = Popen(cmd, creationflags=CREATE_NEW_CONSOLE, stderr=PIPE, shell=True)

        print "hallo"

        with p.stderr:
            for line in iter(p.stderr.readline, b''):
                print line.split('\n')[0]
                self._test_machine_manager.handle_hub_msg(line)
