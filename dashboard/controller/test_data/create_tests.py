import json
from collections import namedtuple

from numpy import random


def create_tests(num_tests, num_machines, num_executable_on):
    test_tuple = namedtuple('test', 'id duration executable_on')

    tests = []

    num_executable_on_list = random.randint(1, num_machines, size=num_tests)

    for i in range(num_tests):
        machines = [0 for _ in range(num_machines)]
        tmp_num_executable_on = num_executable_on if num_executable_on else num_executable_on_list[i]
        while sum(machines) < tmp_num_executable_on:
            machines[random.randint(0, num_machines)] = 1
        machines = [k for k, v in enumerate(machines) if v]
        tests.append(test_tuple(id=i, duration=random.randint(30, 120), executable_on=machines))
    return tests

if __name__ == '__main__':
    num_tests = 200
    num_machines = 10
    num_executable_on = None

    tests = create_tests(num_tests, num_machines, num_executable_on)

    data = {
        'num_machines': num_machines,
        'num_executable_on': num_executable_on,
        'num_tests': num_tests,
        'tests': []
    }
    for test in tests:
        data['tests'].append({
            'id': test.id,
            'duration': test.duration,
            'executable_on': test.executable_on
        })

    print json.dumps(data)

    #f = open('input/do_not_overwrite!_1.json', 'w')
    #f.write(json.dumps(data))
    #f.close()
