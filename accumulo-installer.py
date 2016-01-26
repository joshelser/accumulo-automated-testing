#!/usr/bin/env python

import argparse, glob, logging, os, shutil, subprocess, sys

logger = logging.getLogger(__name__)

def main(**kwargs):
  validate_args(kwargs)

  current_dir = os.path.dirname(os.path.realpath(__file__))
  accumulo_repo = kwargs['accumulo_repo']
  accumulo_home = kwargs['accumulo_home']
  hadoop_home = kwargs['hadoop_home']
  maven_installation = kwargs['maven_installation']
  java_home = kwargs['java_home']

  # Build accumulo
  exit_code = build(accumulo_repo, maven_installation, java_home)
  if exit_code:
    return exit_code

  # Install accumulo
  # TODO Need to support installing to many nodes
  exit_code = install(accumulo_repo, accumulo_home)
  if exit_code:
    return exit_code

  return 0

def validate_args(kwargs):
  accumulo_repo = kwargs['accumulo_repo']
  hadoop_home = kwargs['hadoop_home']
  maven_installation = kwargs['maven_installation']
  java_home = kwargs['java_home']

  # Check that all paths that should be directories are such
  for d in [accumulo_repo, hadoop_home, maven_installation, java_home]:
    assert os.path.isdir(d), "%s is not a directory" % (d)

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

def build(accumulo_repo, maven_installation, java_home):
  env = os.environ.copy()
  env['JAVA_HOME'] = java_home
  env['PATH'] = env['PATH'] + ':' + os.path.join(java_home, 'bin')
  args = [os.path.join(maven_installation, 'bin', 'mvn'), 'package', '-DskipTests', '-Passemble']
  logger.info("Running '%s' in %s" % (' '.join(args), accumulo_repo))
  return subprocess.call(args, cwd=accumulo_repo, env=env)

def install(accumulo_repo, accumulo_home):
  if os.path.exists(accumulo_home):
    logger.info('Removing directory %s' % (accumulo_home))
    shutil.rmtree(accumulo_home)

  logger.info("Creating %s" % (accumulo_home))
  os.makedirs(accumulo_home)
  args = ['tar', 'xf', os.path.join(accumulo_repo, 'assemble', 'target', 'accumulo*.tar.gz'), '--strip', '1', '-C', accumulo_home]
  logger.info("Running '%s'" % (' '.join(args)))
  return subprocess.call(args)

# def remove_bad_symlinks(parent_dir):
#   assert os.path.exists(parent_dir) and os.path.isdir(parent_dir), "%s is not a directory" % parent_dir
#   for filename in os.listdir(parent_dir):
#     full_path = os.path.join(parent_dir, filename)
#     # Try to find symlinks to files that don't exist
#     if os.path.islink(full_path) and not os.path.exists(full_path):
#       logger.info("Removing broken symlink: %s" % full_path)
#       os.remove(full_path)

# def copy_extra_phoenix_libs(hbase_home, phoenix_home):
#   jars_to_link = ['commons-csv-1.0.jar']
#   for jar_to_link in jars_to_link:
#     source = os.path.join(phoenix_home, 'lib', jar_to_link)
#     dest = os.path.join(hbase_home, 'lib', jar_to_link)
#     if not os.path.islink(dest):
#       logger.debug("Symlinking %s to %s" % (source, dest))
#       os.symlink(source, dest)
#
# def restart_queryserver(phoenix_home):
#   assert phoenix_home, "The phoenix home value was undefined"
#   for action in ['stop', 'start']:
#     args = ['su', '-c', '%s %s' % (os.path.join(phoenix_home, 'bin', 'queryserver.py'), action), "-", "hbase"]
#     logger.info("Running %s" % (" ".join(args)))
#     exit_code = subprocess.call(args)
#     # Don't exit if we fail to stop the server, it might not be running
#     if exit_code and action != 'stop':
#       return exit_code
#
#   return 0

def find_java_home():
  dirs = glob.glob('/usr/jdk64/jdk*')
  assert len(dirs) > 0, "Found no JDKs under /usr/jdk64, try specifying by --java_home"
  # first one is the largest (most recent) jdk
  return dirs[0]

if __name__ == '__main__':
  current_dir = os.path.dirname(os.path.realpath(__file__))
  logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

  parser = argparse.ArgumentParser()
  parser.add_argument("--accumulo_home", help="The location to install Accumulo", default="/usr/hdp/current/accumulo-ci")
  parser.add_argument("--hadoop_home", help="The location of the Hadoop installation", default="/usr/hdp/current/hadoop-client/")
  parser.add_argument("--accumulo_repo", help="The location of the Accumulo checkout", default=os.path.join(current_dir, 'accumulo'))
  parser.add_argument('--maven_installation', help="The location of a Maven installation", default=os.path.join(current_dir, 'apache-maven-3.2.5'))
  parser.add_argument('--java_home', help="The location of the Java installation", default=find_java_home())

  args = parser.parse_args()
  # convert the arguments to kwargs
  sys.exit(main(**vars(args)))
