from subprocess import Popen, PIPE
jarfile = r'c:\Users\friend\Downloads\selenium-server-standalone-2.53.0.jar'
ps = r"c:\tools\PsExec.exe"
p = Popen([ps, '\\\\10.0.0.25', '-u', 'friend', '-p', 'friend', '-d', 'java', '-jar', jarfile, '-role', 'node', '-hubHost', '10.0.0.2'], stderr=PIPE, shell=True)
with p.stderr:
    for line in iter(p.stderr.readline, b''):
        print line[:-1]