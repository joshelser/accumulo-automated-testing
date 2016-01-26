#!/usr/bin/env python

import argparse, glob, logging, os, subprocess, sys

logger = logging.getLogger(__name__)

def main(**kwargs):
  validate_args(kwargs)

  print "TODO"

  return 0

def validate_args(kwargs):
  accumulo_home = kwargs['accumulo_home']

  for d in [accumulo_home]:
    assert os.path.isdir(d), "%s is not a directory" % (d)

if __name__ == '__main__':
  current_dir = os.path.dirname(os.path.realpath(__file__))
  logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
  parser = argparse.ArgumentParser()

  parser.add_argument("--accumulo_home", help="The location of the Accumulo installation", default="/usr/hdp/current/accumulo-ci/")

  args = parser.parse_args()
  # convert the arguments to kwargs
  sys.exit(main(**vars(args)))
