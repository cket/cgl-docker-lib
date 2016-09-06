import time
from toil.job import Job
import argparse

def f0(job, cpu=0.1, memory=100):
    time.sleep(20)
    with open("./test", "w") as f:
        f.write("writing forever")

if __name__ == '__main__':

    # Create default options and run
    parser = argparse.ArgumentParser()
    Job.Runner.addToilOptions(parser)
    options = parser.parse_args()

    i = Job.Runner.startToil(Job.wrapJobFn(f0), options)
