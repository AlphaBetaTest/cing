#!/bin/tcsh
# Run like: $CINGROOT/python/Refine/multipleRefineJobs.csh
set stage = rT
set x = 1brv
set ranges = '171-189'

if ( 0 ) then
  set x = LdCof_jfd_ref
  set ranges = '6-23,26-57,63-141'
endif

@ jobCountMax = 5
@ modelCountMax = 10
@ modelsPerJob = $modelCountMax / $jobCountMax
@ jobCount = 0 # default is zero
while ( $jobCount < $jobCountMax )
  @ modelCountStart = $jobCount * $modelsPerJob
  @ modelCountEnd = $modelCountStart + $modelsPerJob - 1
  refine --project $x --name $stage --refine --overwrite --models $modelCountStart"-"$modelCountEnd >& job$jobCount.log &
  sleep 5
  @ jobCount = $jobCount + 1
end

