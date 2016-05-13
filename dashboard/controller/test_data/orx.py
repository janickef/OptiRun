"""
This class uses the OR-Tools library to allocate tests to test machines in such a way that the combined total time used
for search and execution is attempted minimized.
"""

import re
import time
from multiprocessing import Process, Manager, Lock

from ortools.constraint_solver import pywrapcp


class AllocationSolver:

    def __init__(self):
        manager = Manager()

        self._allocations = manager.dict()
        self._max_durations = manager.list()
        self._last_updated = manager.list()

        self._lock = Lock()

    @staticmethod
    def get_durations_and_executable_on(test_list, num_machines):
        """
        This method returns test durations and which machine(s) each test is executable on in the correct format.
        """

        durations = [int(test.duration) for test in test_list]

        executable_on = []
        for test in test_list:
            tmp = []
            for j in range(num_machines):
                if j in test.executable_on:
                    tmp.append(1)
                else:
                    tmp.append(0)
            executable_on.append(tmp)
        return durations, executable_on

    def solve(self, tests, num_machines):
        """
        This method starts the 'find_solution' method as a 'Process' from the 'multiprocessing' library. It continuously
        checks if it is time to terminate the process. When the process has finished or been terminated, the results are
        transformed to the correct format and returned.
        """

        start = time.clock()

        durations, executable_on = self.get_durations_and_executable_on(tests, num_machines)
        num_tests = len(durations)
        num_machines = len(executable_on[0])

        p = Process(
            target=self.find_solution,
            args=(durations, executable_on, self._allocations, self._max_durations, self._last_updated, self._lock)
        )
        p.start()

        while p.is_alive():
            if self._lock.acquire():
                if len(self._last_updated) >= 2:
                    time_since_last_update = self._last_updated[-1]-self._last_updated[-2]
                    if 500*time_since_last_update <= time.clock()-self._last_updated[-1]:
                        p.terminate()
                        break
                    if time_since_last_update >= 10*(self._max_durations[-2]-self._max_durations[-1]):
                        p.terminate()
                        break
                if self._last_updated:
                    time_since_start = time.clock()-start
                    if time_since_start >= 30.0 or time_since_start >= self._max_durations[-1]:
                        p.terminate()
                        break
                self._lock.release()

        allocation_indices_flat = []
        for j in range(num_tests):
            allocation_indices_flat.append([self._allocations[(i, j)] for i in range(num_machines)].index(1))

        return allocation_indices_flat

    def find_solution(self, durations, executable_on, shared_allocations, shared_max_dur, shared_last_updated, lock):
        """
        This method creates an instance of the 'pywrapcp' Solver from the OR-Tools library. It adds constraints and an
        objective to the solver, and searches for the best solution in respect to the objective. Each time a new
        solution has been found, the multiprocessing lock must be acquired before the method can make changes to the
        shared allocations dictionary and the shared max durations and last updated lists.
        """

        solver = pywrapcp.Solver('')

        allocations = {}
        machine_durations = {}

        num_tests = len(durations)
        num_machines = len(executable_on[0])

        for i in range(num_machines):
            for j in range(num_tests):
                allocations[(i, j)] = solver.IntVar(0, 1, "alloc[M%i, T%i]" % (i, j))
                machine_durations[(i, j)] = solver.IntVar(0, durations[j], "durs[M%i, T%i]" % (i, j))

                solver.Add(machine_durations[(i, j)] == allocations[(i, j)] * durations[j])

        allocations_flat = [allocations[(i, j)] for i in range(num_machines) for j in range(num_tests)]
        total_machine_durations_flat = [machine_durations[(i, j)] for i in range(num_machines) for j in
                                        range(num_tests)]

        for i in range(num_machines):
            for j in range(num_tests):
                solver.Add(allocations[(i, j)] <= executable_on[j][i])

        for j in range(num_tests):
            solver.Add(solver.Sum([allocations[i, j] for i in range(num_machines)]) == 1)

        total_durations = []

        for i in range(num_machines):
            total_durations.append(solver.Sum(machine_durations[i, j] for j in range(num_tests)))

        largest_end_time = solver.Max(total_durations)
        objective = solver.Minimize(largest_end_time, 1)

        solution = solver.Assignment()
        solution.Add(allocations_flat)
        solution.Add(total_machine_durations_flat)

        db = solver.Phase(allocations_flat, solver.CHOOSE_RANDOM, solver.ASSIGN_RANDOM_VALUE)
        solver.NewSearch(db, objective)

        while solver.NextSolution():
            lock.acquire()
            for i in range(num_machines):
                for j in range(num_tests):
                    shared_allocations[(i, j)] = int(allocations[(i, j)].Value())

            if num_machines <= 2:
                tmp_max_dur = max([(int(str(t).split(')(')[-1].replace(')', ''))) for t in total_durations])
            else:
                tmp_max_dur = int(re.sub(r'([a-zA-Z()])', '', str(largest_end_time)))

            shared_max_dur.append(tmp_max_dur)
            shared_last_updated.append(time.clock())
            lock.release()
