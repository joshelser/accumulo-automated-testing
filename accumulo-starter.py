#!/usr/bin/env python

import argparse, glob, logging, os, shutil, subprocess, sys

logger = logging.getLogger(__name__)

def main(**kwargs):
  validate_args(kwargs)

  current_dir = os.path.dirname(os.path.realpath(__file__))
  accumulo_home = kwargs['accumulo_home']

  accumulo_password = kwargs['accumulo_password']
  accumulo_instance_name = kwargs['accumulo_instance_name']
  accumulo_hdfs_dir = kwargs['accumulo_hdfs_dir']

  exit_code = initialize(accumulo_home, accumulo_instance_name, accumulo_password, accumulo_hdfs_dir)
  if exit_code:
    return exit_code

  return 0

def validate_args(kwargs):
  accumulo_home = kwargs['accumulo_home']
  assert os.path.isdir(accumulo_home), 'accumulo_home is not a directory'

def copy_if_missing(src, dest):
  '''
  Copy the given src to the dest only if dest does not already exist
  '''
  logger.debug("Attempting to copy %s to %s" % (src, dest))
  if not os.path.exists(dest):
    copy(src, dest)
  else:
    logger.debug("Not copying because %s already exists" % (dest))

def copy_fresh(src, dest):
  if os.path.exists(dest):
    logger.debug("Removing %s" % (dest))
    if os.path.isdir(dest):
      shutil.rmtree(dest)
    else:
      os.remove(dest)

  copy(src, dest)

def copy(src, dest):
  '''
  Copy a source to a destination. The source should exist, the destination should not.
  '''
  assert os.path.exists(src), "Source to copy does not exist: '%s'" % (src)
  assert not os.path.exists(dest), "Destination to copy should not exist: '%s'" % (dest)

  if os.path.isdir(src):
    logger.debug("Copying directory %s to %s" % (src, dest))
    shutil.copytree(src, dest)
  else:
    logger.debug("Copying file %s to %s" % (src, dest))
    shutil.copy(src, dest)

def initialize(accumulo_home, instance_name, password, accumulo_hdfs_dir):
  dir_exists = subprocess.call(['hdfs', 'dfs', '-test', '-d', accumulo_hdfs_dir])
  if 0 == dir_exists:
    logger.info('Deleting ' + accumulo_hdfs_dir)
    subprocess.call(['su', 'hdfs', '-c', 'hdfs dfs -rm -R -skipTrash ' + accumulo_hdfs_dir])

  logger.info("Creating and changing ownership of " + accumulo_hdfs_dir)
  subprocess.call(['su', 'hdfs', '-c', 'hdfs dfs -mkdir ' + accumulo_hdfs_dir])
  subprocess.call(['su', 'hdfs', '-c', 'hdfs dfs -chown accumulo ' + accumulo_hdfs_dir])

  exit_code = subprocess.call([os.path.join(accumulo_home, 'bin', 'accumulo'), 'init', '--clear-instance-name', '--instance-name', instance_name, '--password', password])
  if exit_code:
    return exit_code

  return 0

if __name__ == '__main__':
  current_dir = os.path.dirname(os.path.realpath(__file__))
  logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

  parser = argparse.ArgumentParser()
  parser.add_argument("--accumulo_home", help="The location to install Accumulo", default="/usr/hdp/current/accumulo-ci")

  parser.add_argument("--accumulo_password", help="The Accumulo root user password to set", default="secret")
  parser.add_argument("--accumulo_instance_name", help="The Accumulo instance name", default="accumulo")
  parser.add_argument("--accumulo_hdfs_dir", help="The root directory in HDFS Accumulo will use (verifies)", default="/accumulo")

  args = parser.parse_args()
  # convert the arguments to kwargs
  sys.exit(main(**vars(args)))
