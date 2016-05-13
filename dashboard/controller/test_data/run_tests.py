import json
import time
from collections import namedtuple

from controller.hub.optix import OptiX
from controller.test_data.orx import AllocationSolver

file_name = 'test_set_1.json'


def get_longest_dur(tests, num_machines, allocations):
    total_durations = []
    for i in range(num_machines):
        tmp_tests = [tests[j] for j in range(len(tests)) if allocations[j] == i]
        total_durations.append(sum([test.duration for test in tmp_tests]))
    return max(total_durations)


def print_summary(tests, num_machines, allocations, time_used):
    print "Searching time: %f" % time_used
    print "Execution time: %f" % get_longest_dur(tests, num_machines, allocations)
    print "Total time:     %f" % (time_used + get_longest_dur(tests, num_machines, allocations))


def create_dict(mechanism_name, tests, num_machines, searching_time, execution_time, allocations):
    tmp_data = {
        'mechanism'     : mechanism_name,
        'searching_time': searching_time,
        'execution_time': execution_time,
        'total_time'    : searching_time + execution_time,
        'allocations'   : []
    }

    for i in range(num_machines):
        tmp_allocation = {
            'machine': i,
            'tests'  : []
        }

        for j, test in enumerate(tests):
            if allocations[j] == i:
                tmp_allocation['tests'].append({'id': test.id, 'duration': test.duration})

        tmp_allocation['total_duration'] = sum(t['duration'] for t in tmp_allocation['tests'])

        tmp_data['allocations'].append(tmp_allocation)
    return tmp_data


if __name__ == '__main__':
    test_tuple = namedtuple('test', 'id duration executable_on')

    f = open('input/%s' % file_name, 'r')
    input = json.loads(f.read())
    f.close()

    num_tests = input['num_tests']
    num_machines = input['num_machines']
    num_executable_on = input['num_executable_on']
    tests = [test_tuple(
        id=item['id'],
        duration=item['duration'],
        executable_on=item['executable_on']
    ) for item in input['tests']]

    output = []

    sa = OptiX()
    optix_start = time.clock()
    optix_allocations = sa.solve(tests, num_machines)
    optix_searching_time = time.clock() - optix_start
    optix_execution_time = get_longest_dur(tests, num_machines, optix_allocations)

    output.append(
        create_dict('opti-x', tests, num_machines, optix_searching_time, optix_execution_time, optix_allocations)
    )

    orx = AllocationSolver()
    orx_start = time.clock()
    orx_allocations = orx.solve(tests, num_machines)
    orx_searching_time = time.clock() - orx_start
    orx_execution_time = get_longest_dur(tests, num_machines, orx_allocations)

    output.append(
        create_dict('or-x', tests, num_machines, orx_searching_time, orx_execution_time, orx_allocations)
    )

    print json.dumps(output)

    #f = open('output/do_not_overwrite!_%s' % file_name, 'w')
    #f.write(json.dumps(output))
    #f.close()

    print "OPTI-X"
    print_summary(tests, num_machines, optix_allocations, optix_searching_time)

    print "OR-X"
    print_summary(tests, num_machines, orx_allocations, orx_searching_time)
