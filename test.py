#!/usr/bin/env python 

import os
import main

TESTDIR = 'sample-code'

results = {}
for filename in os.listdir(TESTDIR):
	full_filename = os.path.join(TESTDIR, filename)
	try:
		sim = main.sim_file(full_filename, verbose=False)
		results[filename] = {
			'instructions': sim.instructions_executed(),
			'cycles': sim.cycles_executed(),
			'cpi': sim.cpi(),
		}
	except Exception, e:
		results[filename] = e


for test in sorted(results):
	if not isinstance(results[test], dict):
		print 'Test %s failed with exception %s' % (test, results[test])
	else:
		print 'Test %s succeeded at %d cycles, %d instructions, with %.03f CPI' % (test, results[test]['cycles'], results[test]['instructions'], results[test]['cpi'])
