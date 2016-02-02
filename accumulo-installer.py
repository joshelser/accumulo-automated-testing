#!/usr/bin/env python

import argparse, glob, logging, os, shutil, subprocess, sys

logger = logging.getLogger(__name__)

def main(**kwargs):
  validate_args(kwargs)

  current_dir = os.path.dirname(os.path.realpath(__file__))
  accumulo_tarball = kwargs['accumulo_tarball']
  accumulo_home = kwargs['accumulo_home']
  accumulo_site_file = kwargs['accumulo_site_file']
  accumulo_env_file = kwargs['accumulo_env_file']
  accumulo_masters_file = kwargs['accumulo_masters_file']
  accumulo_monitor_file = kwargs['accumulo_monitor_file']
  accumulo_tracers_file = kwargs['accumulo_tracers_file']
  accumulo_slaves_file = kwargs['accumulo_slaves_file']

  # Make sure the accumulo user exists and such
  exit_code = setup_accumulo_user()
  if exit_code:
    return exit_code

  # Install accumulo
  exit_code = install(accumulo_tarball, accumulo_home, accumulo_site_file, accumulo_env_file, accumulo_masters_file, accumulo_monitor_file, accumulo_tracers_file, accumulo_slaves_file)
  if exit_code:
    return exit_code

  return 0

def validate_args(kwargs):
  accumulo_tarball = kwargs['accumulo_tarball']
  accumulo_site_file = kwargs['accumulo_site_file']
  accumulo_env_file = kwargs['accumulo_env_file']
  accumulo_masters_file = kwargs['accumulo_masters_file']
  accumulo_monitor_file = kwargs['accumulo_monitor_file']
  accumulo_tracers_file = kwargs['accumulo_tracers_file']
  accumulo_slaves_file = kwargs['accumulo_slaves_file']

  # Check that all files are actually files
  for f in [accumulo_tarball, accumulo_site_file, accumulo_env_file, accumulo_masters_file, accumulo_monitor_file, accumulo_tracers_file, accumulo_slaves_file]:
    assert os.path.isfile(f), '%s is not a file' % (f)

def setup_accumulo_user():
  stdout = subprocess.check_output(['awk', "-F", ':', '{print $1}', "/etc/passwd"])
  users = stdout.split("\n")
  if not 'accumulo' in users:
    return create_accumulo_user()

  return 0

def create_accumulo_user():
  limits_dir = '/etc/security/limits.d'
  limits_file = os.path.join(limits_dir, 'accumulo.conf')
  if not os.path.isfile(limits_file):
    logger.debug("Creating limits file for Accumulo")
    if not os.path.isdir(limits_dir):
      os.makedirs(limits_dir)
    with open(limits_file, 'w') as f:
      f.write('accumulo - nofile 65536')

  logger.debug("Creating accumulo user")
  return subprocess.call(['useradd', '-m', 'accumulo'])

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

def install(accumulo_tarball, accumulo_home, accumulo_site_file, accumulo_env_file, accumulo_masters_file, accumulo_monitor_file, accumulo_tracers_file, accumulo_slaves_file):
  if os.path.exists(accumulo_home):
    logger.info('Removing directory %s' % (accumulo_home))
    shutil.rmtree(accumulo_home)

  logger.info("Creating %s" % (accumulo_home))
  os.makedirs(accumulo_home)

  args = ['tar', 'xf', accumulo_tarball, '--strip', '1', '-C', accumulo_home]
  logger.info("Running '%s'" % (' '.join(args)))
  exit_code = subprocess.call(args)
  if exit_code:
    return exit_code

  # Configuration files
  accumulo_conf_dir = os.path.join(accumulo_home, 'conf')
  example_conf_dir = os.path.join(accumulo_conf_dir, 'examples', '3GB', 'native-standalone')

  # Copy the provided (or generated files)
  for config_file in [accumulo_site_file, accumulo_env_file, accumulo_masters_file, accumulo_monitor_file, accumulo_tracers_file, accumulo_slaves_file]:
    copy(config_file, os.path.join(accumulo_conf_dir, os.path.basename(config_file)))

  # Copy the others from the examples that we don't care about
  for example_file in ['auditLog.xml', 'generic_logger.xml', 'log4j.properties', 'client.conf', 'monitor_logger.xml', 'hadoop-metrics2-accumulo.properties']:
    copy(os.path.join(example_conf_dir, example_file), os.path.join(accumulo_conf_dir, example_file))

  logger.info("TODO Build the native maps")

  return subprocess.call(['chown', '-R', 'accumulo', accumulo_home])

if __name__ == '__main__':
  current_dir = os.path.dirname(os.path.realpath(__file__))
  logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

  parser = argparse.ArgumentParser()
  parser.add_argument("--accumulo_tarball", help="An Accumulo tarball to install", default=None)
  parser.add_argument("--accumulo_home", help="The location to install Accumulo", default="/usr/hdp/current/accumulo-ci")
  parser.add_argument("--accumulo_site_file", help="The accumulo-site.xml file to install", default=os.path.join(current_dir, 'accumulo-site.xml'))
  parser.add_argument("--accumulo_env_file", help="The accumulo-site.xml file to install", default=os.path.join(current_dir, 'accumulo-env.sh'))

  parser.add_argument("--accumulo_masters_file", help="The masters file to install", default=os.path.join(current_dir, 'masters'))
  parser.add_argument("--accumulo_monitor_file", help="The monitor file to install", default=os.path.join(current_dir, 'monitor'))
  parser.add_argument("--accumulo_tracers_file", help="The tracers file to install", default=os.path.join(current_dir, 'tracers'))
  parser.add_argument("--accumulo_slaves_file", help="The slaves file to install", default=os.path.join(current_dir, 'slaves'))

  args = parser.parse_args()
  # convert the arguments to kwargs
  sys.exit(main(**vars(args)))
