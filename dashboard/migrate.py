import subprocess
import re

p = subprocess.Popen(('python', 'manage.py', 'makemigrations', 'testautomation'), stdout=subprocess.PIPE)
p.wait()
out, err = p.communicate()

mig = str.split(out, "_")[0]
try:
    migration_id = re.findall(r'\b\d+\b', mig)[0]
    print "migration_id", migration_id
    p = subprocess.Popen(('python', 'manage.py', 'sqlmigrate', 'testautomation', migration_id))
    p.wait()
except:
    migration_id = 0

p = subprocess.Popen(('python', 'manage.py', 'migrate'))
p.wait()
