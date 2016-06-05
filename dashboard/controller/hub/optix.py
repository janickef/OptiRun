"""
This class uses the Opti-X algorithm to allocate tests to test machines in such a way that the combined total time used
for search and execution is attempted minimized.
"""

import itertools
import time
from collections import namedtuple
from random import choice


class OptiX:
    def __init__(self):
        self.test = namedtuple('Test', 'id duration executable_on')

        self._MACHINE = "machine"
        self._TEST_SET = "test_set"
        self._TOT_DUR = "total_duration"

        self._timeout = 30.0

    def allocate(self, ms, ts):
        print "Allocating tests..."

        tests, non_executables = self.tuplify(ms, ts)
        non_executables = [ts[item.id] for item in non_executables]

        allocation_indices = self.solve(tests, len(ms))
        allocations = self.post_process(allocation_indices, ms, tests, ts)

        print "Allocation finished."
        self.print_result(allocations, non_executables)
        return non_executables, allocations

    def solve(self, tests, num_machines):
        """
        This method call the 'init_allocation' and 'iterate' methods and returns the allocation result.
        """

        tests = self.sort_tests(tests, num_machines)
        allocation_indices = self.init_allocation(tests, num_machines)
        tests.sort(key=lambda x: x.id)
        allocation_indices = self.iterate(tests, allocation_indices, num_machines)

        return allocation_indices

    def tuplify(self, ms, ts):
        """
        This method creates a named tuple of each test, containing only the information needed during the allocation,
        to make the test list as light weight as possible. This information includes the index of the test in the
        original test list, the duration of the test, and a list of the machines the test can be executed on.
        """

        tests = []
        non_executables = []
        for i, test in enumerate(ts):
            tmp_test = self.test(id=i, duration=test.duration, executable_on=[])
            for j, machine in enumerate(ms):
                if test.browser.lower() == 'any':
                    tmp_test.executable_on.append(j)
                    continue
                machine_browsers = [mb['browser'].lower() for mb in machine.browsers]
                if test.browser.lower() in machine_browsers:
                    tmp_test.executable_on.append(j)
            if tmp_test.executable_on:
                tests.append(tmp_test)
            else:
                non_executables.append(tmp_test)
        return tests, non_executables

    @staticmethod
    def sort_tests(tests, num_machines):
        """
        This method sorts the tests in such a way that the initial allocation will be as effective as possible. The
        tests are first grouped by how many test machines they are executable on. The tests that are not executable on
        any machines are placed in a separate list. The groups are then looped through, starting with the smallest
        number of machines, and sorted by duration in descending order. The tests are then assembled back to a list and
        returned together with the non-executable tests.
        """

        tmp_tests = []

        for i in range(0, num_machines + 1):
            tmp = [test for test in tests if len(test.executable_on) == i]
            tmp.sort(key=lambda t: t.duration, reverse=True)
            tmp_tests.append(tmp)

        tests = []
        for tt in tmp_tests:
            tests += tt

        return tests

    @staticmethod
    def init_allocation(tests, num_machines):
        """
        This function performs the initial test allocation by looping through the test list and assigning each test
        to the machine that currently has the shortest total execution time among the machines that the test is
        executable on.
        """

        allocation_indices = {test.id: 0 for test in tests}
        total_durations = [0.0 for _ in range(num_machines)]

        for i, test in enumerate(tests):
            shortest_idx = test.executable_on[0]
            for x in test.executable_on:
                if total_durations[x] < total_durations[shortest_idx]:
                    shortest_idx = x
            total_durations[shortest_idx] += test.duration
            allocation_indices[test.id] = shortest_idx
        return allocation_indices

    def iterate(self, tests, allocation_indices, num_machines):
        """
        This method finds the test machine with the longest total execution time, loops through the remaining test
        machines in an attempt to identify the two subsets that when swapped will provide the largest enhancement in
        overall total duration. This is repeated until the method can no longer find an enhanced solution or one of the
        stop criteria is met.
        """

        if not allocation_indices:
            return allocation_indices

        start = time.clock()

        durations = self.get_total_durations(tests, allocation_indices, num_machines)
        longest_duration = max(durations)

        best_case_goal = sum(durations) / len(durations)
        best_case_win = longest_duration - best_case_goal

        allocation_no = 0

        while True:
            durations = self.get_total_durations(tests, allocation_indices, num_machines)
            longest_duration = max(durations)
            x = durations.index(longest_duration)

            allocation_no += 1
            print allocation_no, longest_duration

            new_longest_duration = longest_duration

            for i in range(num_machines):
                if i == x:
                    continue

                loop_start = time.clock()

                best_case_swap_goal = (durations[i]+durations[x])/2
                best_case_swap_win = durations[x] - best_case_swap_goal

                swapper_subsets = self.get_subsets(tests, allocation_indices, x, i)
                swapper_subsets.sort(key=lambda t: t.total_duration, reverse=True)

                swappee_subsets = self.get_subsets(tests, allocation_indices, i, x)
                swappee_subsets.sort(key=lambda t: t.total_duration)

                for j, swapper_subset in enumerate(swapper_subsets):
                    br = False

                    swapper_subset_dur = swapper_subset.total_duration
                    swapper_init_dur = longest_duration - swapper_subset_dur

                    for k, swappee_subset in enumerate(swappee_subsets):
                        swappee_subset_dur = swappee_subset.total_duration

                        if swapper_subset_dur == swappee_subset_dur:
                            br = True
                            break

                        swappee_init_dur = durations[i] - swappee_subset_dur

                        new_swapper_dur = swapper_init_dur + swappee_subset_dur
                        new_swappee_dur = swappee_init_dur + swapper_subset_dur

                        if new_swappee_dur < new_longest_duration and new_swapper_dur < new_longest_duration:
                            swapper_swapset = swapper_subset
                            swappee_swapset = swappee_subset
                            swappee_idx = i
                            new_longest_duration = max(new_swapper_dur, new_swappee_dur)

                    if br or swapper_init_dur >= new_longest_duration or time.clock()-loop_start >= best_case_swap_win:
                        break

                if time.clock()-start >= best_case_win or time.clock()-start >= self._timeout:
                    break

            if new_longest_duration < longest_duration and swapper_swapset and swappee_swapset and swappee_idx:
                for test in swapper_swapset.subset:
                    allocation_indices[test.id] = swappee_idx

                for test in swappee_swapset.subset:
                    allocation_indices[test.id] = x
            else:
                break

        return allocation_indices

    def print_result(self, allocations, non_executables):
        """
        This method prints the allocation result.
        """

        print "\nAllocations"
        for i, a in enumerate(allocations):
            print "Machine %i (%ds):" % (i, a[self._TOT_DUR])
            if a[self._TEST_SET]:
                for t in a[self._TEST_SET]:
                    print "%s (%ss);" % (t.title, t.duration),
                print
            else:
                print "<Empty>"
        if non_executables:
            print "Non-Executable Tests:"
            for t in non_executables:
                print t

    def post_process(self, allocation_indices, ms, tests, ts):
        """
        This method post-processes the allocation result, which is currently just a list of numbers, on for each test,
        referring to the index of the test machine that the test is allocated to, and creates a dictionary in the
        correct format required by the test executor.
        """

        allocations = []
        for i, m in enumerate(ms):
            if m.browsers:
                tmp_tests = []
                tot_dur = 0.0

                for t in tests:
                    if allocation_indices[t.id] == i:
                        if ts[t.id].browser == 'any':
                            ts[t.id].set_browser(choice(m.browsers)['browser'])
                        tmp_tests.append(ts[t.id])
                        tot_dur += t.duration

                allocations.append({
                    self._MACHINE: m,
                    self._TEST_SET: tmp_tests,
                    self._TOT_DUR: tot_dur,
                })
        return allocations

    @staticmethod
    def get_subsets(tests, allocation_indices, idx1, idx2):
        """
        This method takes the test list and filters it to contain only the tests that are currently allocated to the
        test machine with index idx1, but can also be executed on the machine with index idx2. It then creates a list of
        subsets from the filtered test list. The maximum size of the subsets are determined by the number of tests in
        the filtered test list, x; the max size is x if x < 10, 20 - x if 10 <= x < 20 and 1 if 20 < x. This is to avoid
        spending vast amounts of time and possibly experience memory leaks.
        """

        tests = [t for t in tests if idx2 in t.executable_on and allocation_indices[t.id] == idx1]

        num_tests = len(tests)
        max_subset_size = num_tests if num_tests < 10 else 20 - num_tests if num_tests < 20 else 1

        subset_tuple = namedtuple('Subset', 'subset total_duration')

        subsets = [subset_tuple(subset=[], total_duration=0.0)]

        if max_subset_size == 1:
            for t in tests:
                subsets.append(subset_tuple(subset=[t], total_duration=t.duration))
        else:
            for j in range(1, min(max_subset_size, len(tests)) + 1):
                for subset in itertools.combinations(tests, j):
                    tmp_subset = []
                    for s in subset:
                        tmp_subset.append(s)
                    subsets.append(subset_tuple(subset=tmp_subset, total_duration=sum([t.duration for t in tmp_subset])))
        return subsets

    @staticmethod
    def get_total_durations(tests, allocation_indices, num_machines):
        """
        This method returns a list with one entry for each test machine, containing the sum of the durations of the
        tests allocated to the test machine in question.
        """

        return [sum([test.duration for test in tests if allocation_indices[test.id] == i]) for i in range(num_machines)]

