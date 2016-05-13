import paramiko
import sys
import threading

def console_print(std):
    with std:
        for line in iter(std.readline, b''):
            print line

nbytes = 4096

hostname = 'opti-VirtualBox'
hostname = '10.0.0.15'
port = 22
username = 'opti'
password = 'opti'
#command = 'xvfb-run java -jar "/home/opti/Dropbox/OptiRun/selenium-server-standalone-2.51.0.jar" -role node -hubHost lnor010710 -uuid 52b4ce9e-fb3a-11e5-b096-080027f8a664 -browser "browserName=chrome,version=49.0.2623.110,applicationName=52b4ce9e-fb3a-11e5-b096-080027f8a664" -Dwebdriver.chrome.driver=/home/opti/Dropbox/OptiRun/drivers/chromedriver -browser "browserName=firefox,version=45.0,applicationName=52b4ce9e-fb3a-11e5-b096-080027f8a664"'
#command = '/home/opti/Dropbox/OptiRun/run.sh'
#command = 'xclock'

command = 'ifconfig'

interface = paramiko.SSHClient()
#snip the connection setup portion


client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

client.connect(hostname, port, username=username, password=password)
#stdin, stdout, stderr = client.exec_command("export DISPLAY=:0.0")
stdin, stdout, stderr = client.exec_command(command)

with stderr:
    for line in iter(stderr.readline, b''):
        print line.replace('\n', '')

"""
out_thread = threading.Thread(target=console_print, args=(stdout,))
out_thread.start()


in_thread = threading.Thread(target=console_print, args=(stdin,))
in_thread.start()

err_thread = threading.Thread(target=console_print, args=(stderr,))
err_thread.start()
"""
"""
for line in stdout.readlines():
    print line

for line in stdin.readlines():
    print line

for line in stderr.readlines():
    print line
"""
client.close()
