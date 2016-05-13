
    """
    def allocate_scripts(self, ms, ts):
        allocations = self.create_allocation_list(ms)
        tests = self.create_test_list(allocations, ts)
        non_executables, tests = self.sort_tests(allocations, tests)

        for t in tests:
            print t[self._TEST]

        print "\n\n\n"

        allocations = self.inital_allocation(allocations, tests)

        self.print_allocations(allocations, tests)

        allocations = self.iterate(allocations, tests)

        for m in allocations:
            for t in m[self._TEST_SET]:
                if t.browser.lower() == self._ANY:
                    t.set_browser(random.choice([browser['browser'] for browser in m[self._MACHINE].browsers]))

        print "\n*****************************************************************************\n"

        self.print_allocations(allocations, tests)

        longest = allocations[self.get_glob_max_idx(allocations)]
        print self.tot_dur(longest[self._TEST_SET])

        return non_executables, allocations

    def print_allocations(self, allocations, tests):
        for m in allocations:
            print "Machine " + m[self._MACHINE].url + " " + m[self._MACHINE].platform['os'] + ",", [browser['browser'] for browser in m[self._MACHINE].browsers], "(" + str(
                m[self._TOT_DUR]) + "s):"
            tmp_tests = [t for t in m[self._TEST_SET]]
            for tmp_t in tmp_tests:
                for t in tests:
                    if tmp_t == t[self._TEST]:
                        print t[self._TEST]
                        # print t[self._TEST].estimated_duration, t[self._TEST].browser, t[self._TEST].platform, t[self._EXECUTABLE_ON]
                        break

    def sort_tests(self, allocations, tests):
        non_executables = []
        tmp_tests = []

        for i in range(0, len(allocations) + 1):
            tmp = [test for test in tests if len(test[self._EXECUTABLE_ON]) == i]
            if i == 0:
                non_executables = [t[self._TEST] for t in tmp]
            else:
                tmp.sort(key=lambda t: t[self._TEST].estimated_duration, reverse=True)
                tmp_tests.append(tmp)

        tests = []
        for tt in tmp_tests:
            tests += tt

        return non_executables, tests

    def create_allocation_list(self, ms):
        allocations = []
        for m in ms:
            if m.browsers:
                allocations.append({
                    self._MACHINE:  m,
                    self._TEST_SET: [],
                    self._TOT_DUR:  0,
                })
        #print allocations
        return allocations

    def create_test_list(self, allocations, ts):
        tests = []
        for t in ts:
            test = {
                self._TEST         :                 t,
                self._EXECUTABLE_ON: []
            }

            for allocation in allocations:
                #print "BROWSERS IN M:", allocation[self._MACHINE].browsers
                #print "BROWSER: ", t.browser, [b['browser'] for b in allocation[self._MACHINE].browsers]
                #print "PLATFORM:", t.platform, allocation[self._MACHINE].platform['os']
                #print type(t.browser)
                if (t.browser.lower() in [browser.lower() for browser in [b['browser'] for b in allocation[self._MACHINE].browsers]] or t.browser.lower() == self._ANY) and (t.platform.lower() == allocation[self._MACHINE].platform['os'].lower() or t.platform.lower() == self._ANY):
                    test[self._EXECUTABLE_ON].append(allocations.index(allocation))
            tests.append(test)

        return tests

    @staticmethod
    def tot_dur(tests):
        tot = 0
        for test in tests:
            #print test, test.estimated_duration, type(test.estimated_duration)
            tot += float(test.estimated_duration)
        return tot

    def inital_allocation(self, allocations, tests):
        # This function performs the initial test allocation

        for t in tests:
            shortest_dur = float(sys.maxint)
            shortest_dur_idx = 0

            compatible_machine_indices = t[self._EXECUTABLE_ON]

            for i, idx in enumerate(compatible_machine_indices):
                tmp_dur = self.tot_dur(allocations[idx][self._TEST_SET])
                if tmp_dur < shortest_dur:
                    shortest_dur_idx = idx
                    shortest_dur     = tmp_dur
            allocations[shortest_dur_idx][self._TEST_SET].append(t[self._TEST])

        for m in allocations:
            m[self._TOT_DUR] = self.tot_dur(m[self._TEST_SET])

        return allocations

    def get_subsets(self, allocations, tests, idx1, idx2):
        # The following line creates a list of tests that are currently allocated to the machine with index idx1 and
        # are also executable on the machine with index idx2.
        tests = [
            t[self._TEST] for t in tests
            if idx2 in t[self._EXECUTABLE_ON] and t[self._TEST] in allocations[idx1][self._TEST_SET]
            ]

        length = len(tests)
        if length < 10:
            max_subset_size = length
        elif length < 20:
            max_subset_size = 20-length
        else:
            max_subset_size = 1

        # print "Number of tests:", length, "Max subset size:", max_subset_size

        # Creating a list of dictionaries containing a subset of tests and the total duration of the subset.
        subsets = [{
            self._TEST_SET:  [],
            self._TOT_DUR: 0
        }]

        if max_subset_size == 1:
            for t in tests:
                subsets.append({
                    self._TEST_SET:   [t],
                    self._TOT_DUR: t.estimated_duration
                })
        else:
            for j in range(1, min(max_subset_size, len(tests)) + 1):
                for subset in set(itertools.combinations(tests, j)):
                    subsets.append({
                        self._TEST_SET:   list(subset),
                        self._TOT_DUR: self.tot_dur(list(subset))
                    })
        return subsets

    def get_glob_max_idx(self, allocations):
        glob_max = 0
        glob_max_idx = 0
        for i, m in enumerate(allocations):
            if m[self._TOT_DUR] > glob_max:
                glob_max     = m[self._TOT_DUR]
                glob_max_idx = i
        return glob_max_idx

    def iterate(self, allocations, tests):
        # This function performs the remaining iterations
        tot_start         = time.clock()
        tot_saved_time    = 0
        iteration_counter = 0

        if not allocations:
            return allocations

        init_glob_max_idx = self.get_glob_max_idx(allocations)
        init_glob_max = allocations[init_glob_max_idx][self._TOT_DUR]

        glob_durs = [d[self._TOT_DUR] for d in allocations]
        abs_goal = float(sum(glob_durs))/len(glob_durs)

        tot_max = max(float(dur) for dur in [d[self._TOT_DUR] for d in allocations])

        tot_max_win = tot_max-abs_goal

        #print tot_max
        #print abs_goal
        #print tot_max_win
        #print float(tot_max/10000)

        #sys.exit(0)

        if float(tot_max/10000) > tot_max_win:
            return allocations
            #print float(tot_max/10000), tot_max_win, "necessary?"

        while True:
            print "hello"
            it_start = time.clock()
            iteration_counter += 1
            #print "\n\n\n* ITERATION", iteration_counter, "*"
            # allocations.sort(key=lambda x: x[self._TOT_DUR])

            glob_max_idx  = self.get_glob_max_idx(allocations)
            glob_max      = allocations[glob_max_idx][self._TOT_DUR]
            new_glob_max  = glob_max
            prev_glob_max = glob_max

            #print "Swapper: Machine", allocations[glob_max_idx][self._MACHINE], "Dur:", allocations[glob_max_idx][self._TOT_DUR]

            for i, m in enumerate(allocations):
                if i == glob_max_idx:
                    print i
                    continue

                loop_start = time.clock()

                swapper_subsets = self.get_subsets(allocations, tests, glob_max_idx, i)
                swapper_subsets.sort(key=lambda x: x[self._TOT_DUR], reverse=True)

                swappee_subsets = self.get_subsets(allocations, tests, i, glob_max_idx)
                swappee_subsets.sort(key=lambda x: x[self._TOT_DUR])

                """"""
                #print "OLD SWAPPER:"
                #for t in swapper_subsets:
                #   print t[self._TEST]
                #    print t

                #print "OLD SWAPPEE:"
                #for t in swappee_subsets:
                #   print t[self._TEST]
                #    print t
                #""""""

                diff = float(allocations[glob_max_idx][self._TOT_DUR] - allocations[i][self._TOT_DUR])
                max_win = diff/2
                #print "swapper tot dur:", allocations[glob_max_idx][self._TOT_DUR]
                #print "swappee tot dur:", allocations[i][self._TOT_DUR]
                #print "diff:", diff
                #print "max win:", max_win

                # Finding the swap that decreases the global duration as much as possible
                for j, swapper_subset in enumerate(swapper_subsets):
                    swapper_subset_dur = swapper_subset[self._TOT_DUR]
                    swapper_init_dur   = glob_max - swapper_subset_dur

                    break_val = False

                    for k, swappee_subset in enumerate(swappee_subsets):
                        swappee_subset_dur = swappee_subset[self._TOT_DUR]

                        #if swappee_subset_dur == swapper_subset_dur:
                        #    print 3
                        #    break_val = True
                        #    break

                        swappee_init_dur = m[self._TOT_DUR] - swappee_subset_dur

                        new_swapper_dur  = swapper_init_dur + swappee_subset_dur
                        new_swappee_dur  = swappee_init_dur + swapper_subset_dur

                        if new_swappee_dur < new_glob_max and new_swapper_dur < new_glob_max:
                            #print "Changing", [t.estimated_duration for t in swapper_subset[self._TEST_SET]], "With",\
                            #    [t.estimated_duration for t in swappee_subset[self._TEST_SET]]
                            #print ">>> New global max:", max(new_swapper_dur, new_swappee_dur)

                            new_glob_max = max(new_swapper_dur, new_swappee_dur)
                            swapper_swap = swapper_subset
                            swappee_swap = swappee_subset
                            swappee_idx  = i

                        if (time.clock() - loop_start) >= (diff / 2):
                            #print "BREAKING! Max win:", max_win, "time since loop start:", time.clock() - it_start
                            break_val = True
                            print 2
                            break

                        #if (time.clock()-loop_start) >= max_win:
                            #print "**********************************************************************"
                        #print "max win:", max_win, "time since loop start:", time.clock() - start
                        #if new_swapper_dur > new_glob_max:
                        #    break_val = True
                        #    print new_swapper_dur
                        #    break

                    if break_val:
                        print "OK1"
                        break

                    if swapper_init_dur >= new_glob_max:
                        print "OK2"
                        break

                if (time.clock()-tot_start) >= tot_max_win:
                    #print "Passed max total win"
                    print "OK"
                    break



                    # if (time.clock() - it_start) >= (diff / 2):
                    #   break

            if new_glob_max < glob_max:
                """"""
                print "*** SWAPPER - Machine " + allocations[glob_max_idx][self._ID] + " ***"
                print "BEFORE:", sorted([t.estimated_duration for t in allocations[glob_max_idx][self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in allocations[glob_max_idx][self._TEST_SET]])) + ")"
                print "REMOVING:", sorted([t.estimated_duration for t in swapper_swap[self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in swapper_swap[self._TEST_SET]])) + ")"
                print "ADDING:", sorted([t.estimated_duration for t in swappee_swap[self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in swappee_swap[self._TEST_SET]])) + ")"
                """"""

                allocations[glob_max_idx][self._TEST_SET]   = [test for test in allocations[glob_max_idx][self._TEST_SET] if
                                                       test not in swapper_swap[self._TEST_SET]]
                allocations[glob_max_idx][self._TEST_SET]  += swappee_swap[self._TEST_SET]
                allocations[glob_max_idx][self._TOT_DUR] = self.tot_dur(allocations[glob_max_idx][self._TEST_SET])

                """"""
                print "AFTER:", sorted([t.estimated_duration for t in allocations[glob_max_idx][self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in allocations[glob_max_idx][self._TEST_SET]])) + ")"

                print"\n"
                print "*** SWAPPEE - Machine " + allocations[swappee_idx][self._ID] + " ***"
                print "BEFORE:", sorted([t.estimated_duration for t in allocations[swappee_idx][self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in allocations[swappee_idx][self._TEST_SET]])) + ")"
                print "REMOVING:", sorted([t.estimated_duration for t in swappee_swap[self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in swappee_swap[self._TEST_SET]])) + ")"
                print "ADDING:", sorted([t.estimated_duration for t in swapper_swap[self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in swapper_swap[self._TEST_SET]])) + ")"
                """"""

                allocations[swappee_idx][self._TEST_SET] = [test for test in allocations[swappee_idx][self._TEST_SET] if
                                                      test not in swappee_swap[self._TEST_SET]]
                allocations[swappee_idx][self._TEST_SET] += swapper_swap[self._TEST_SET]
                allocations[swappee_idx][self._TOT_DUR] = self.tot_dur(allocations[swappee_idx][self._TEST_SET])

                """"""
                print "AFTER:", sorted([t.estimated_duration for t in allocations[swappee_idx][self._TEST_SET]]), \
                    "(SUM:", str(sum([t.estimated_duration for t in allocations[swappee_idx][self._TEST_SET]])) + ")"

                print "\nSaved " + str(glob_max - new_glob_max) + "s\n"
                """"""
                tot_saved_time += (prev_glob_max - new_glob_max)

                for m in allocations:
                    m[self._TOT_DUR] = self.tot_dur(m[self._TEST_SET])
                    #print "Machine " + m[self._MACHINE].url + ", Duration after " + str(
                    #    iteration_counter) + " iteration: " + str(m[self._TOT_DUR]) + "s)"
            else:
                #print "break 1"
                break

            iteration_dur = time.clock() - it_start
            #print "Iteration took", iteration_dur, "seconds"

            # if time.clock()-start >= glob_max-new_glob_max:
            #    print "break 2"
            #    break

        final_glob_max = allocations[self.get_glob_max_idx(allocations)][self._TOT_DUR]
        calculation_time = time.clock() - tot_start

        #print "\n"
        #print "Number of iterations:    ", iteration_counter
        #print "Total time saved:        ", tot_saved_time
        #print "Actual time saved:       ", init_glob_max - final_glob_max
        #print "Net time saved:          ", init_glob_max - final_glob_max - calculation_time
        #print "Time used:               ", calculation_time
        #print "Initial execution time:  ", init_glob_max
        #print "Enhanced execution time: ", final_glob_max

        return allocations
    """