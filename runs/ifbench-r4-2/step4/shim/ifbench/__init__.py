"""Shim of the reference `ifbench` package used to run the reference's unit
tests (audit/step4/instructions_test.py, an unmodified copy) against another
implementation. IFB_TARGET selects it: reference | grader | replacement.

`instructions_util` and `classic_instructions` are the reference's own code.
In `instructions`, every IFBench class keeps the reference's build_description;
check_following is routed to the target.
"""
