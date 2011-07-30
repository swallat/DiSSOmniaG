# -*- coding: utf-8 -*-
"""
Created on 25.07.2011

@author: Sebastian Wallat
"""

import sys, logging
from dissomniag.dbAccess import Session

log = logging.getLogger("utils.wrapper")


"""
Rewrite
Synchronization decorator
  This decorator can be used to synchronize method calls. Synchronization is relative to 
  some kind of lock. Before each function call the acquire method of the lock is called,
  and after the function call the release method is called regardless of exceptions.

Example:
  @synchronized(threading.Lock())
  def critical():
    ...critical_block...
"""
def synchronized(conditionOrLock):
    def wrap(fn):
        def call(*args, **kwargs):
            with conditionOrLock:
                return fn(*args, **kwargs)
        call.__name__ = fn.__name__
        call.__doc__ = fn.__doc__
        call.__dict__.update(fn.__dict__)
        return call
    return wrap

#===============================================================================
# The following part is an excerption from the ToMaTo Project
#===============================================================================


"""
Detach decorator
  This decorator can be used to run functions in parallell to normal execution.
  For each function call a new thread is created to execute the function call.
  
Example:
  @detached
  def long_function():
    ...long_function...
"""
def detached(fn):
    from thread import start_new_thread
    def call(*args, **kwargs):
        return start_new_thread(fn, args, kwargs)
    call.__name__ = fn.__name__
    call.__doc__ = fn.__doc__
    call.__dict__.update(fn.__dict__)
    return call


"""
Every decorator
  This decorator can be used to run a method periodically. The period can be given as a
  combination as seconds, millis, minutes, hours and days as kwargs. The method will be
  repeated until the main thread exits.
  
Example:
  @every(minutes=30, hours=1)
  def housekeeping():
    ...some_periodic_task...
"""
def every(seconds = 0, millis = 0, minutes = 0, hours = 0, days = 0):
    from thread import start_new_thread
    from time import sleep
    import atexit
    period = millis / 1000 + seconds + 60 * (minutes + 60 * (hours + 24 * days)) 
    def wrap(fn):
        running = True
        def run():
            while running:
                sleep(period)
                fn()
        def stop():
            running = False
        start_new_thread(run, ())
        atexit.register(stop)
        return fn
    return wrap


"""
Profile decorator
  This decorator can be used to profile a method. The output filename can be given
  as a parameter. If the additional appendDate is given, the current date at the time
  of execution is appended to the filename.
  
Example:
  @profile(outfile)
  def profileme():
    ...some_cpu_intensive_task...
"""
def profile(out, appendDate = False):
    try:
        import cProfile as profile
    except:
        import profile
    if appendDate:
        import datetime
    def wrap(fn):
        def call(*args, **kwargs):
            ldict = locals().copy()
            ldict.update({"fn": fn, "args": args, "kwargs": kwargs})
            if appendDate:
                out = "%s-%s" % (out, datetime.datetime.now().isoformat())
            profile.runctx("rtn = fn(*args, **kwargs)", globals(), ldict, out)
            return ldict["rtn"]
        call.__name__ = fn.__name__
        call.__doc__ = fn.__doc__
        call.__dict__.update(fn.__dict__)
        return call
    return wrap

#===============================================================================
# End of ToMaTo excerption
#===============================================================================


def wrap_db(func):
    def callFunc(*args, **kwargs):
        session = Session()
        f = func(*args, **kwargs)
        session.commit()
        Session.remove()
        return f
    return callFunc
