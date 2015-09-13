#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, with_statement

import os
import sys
from fabric.api import env, local, task, settings
from fabric.colors import blue, red
import fabric.contrib.project as project
from simiki import config

# XXX must run fab in root path of wiki
configs = config.parse_config('_config.yml')

env.colorize_errors = True


def do_exit(msg):
    print(red(msg))
    print(blue('Exit!'))
    sys.exit()


# cannot put this block in deploy_rsync() for env.hosts
if 'rsync' in configs:
    rsync_configs = configs['rsync']
    if not isinstance(rsync_configs, dict):
        do_exit('Warning: rsync not set right in _config.yml')

    env.user = rsync_configs.get('user', 'root')
    # Remote host and username
    if 'host' not in rsync_configs:
        do_exit('Warning: rsync host not set in _config.yml!')
    env.hosts = [rsync_configs['host'],]

    # Local output path
    env.local_output = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        configs['destination'])

    # Remote path to deploy output
    if 'dir' not in rsync_configs:
        do_exit('Warning: rsync dir not set in _config.yml!')
    env.remote_output = rsync_configs['dir']

    # Other options
    env.port = rsync_configs.get('port')
    env.rsync_delete = rsync_configs.get('delete', False)


def deploy_rsync():
    '''for rsync'''
    project.rsync_project(
        local_dir=env.local_output.rstrip("/")+"/",
        remote_dir=env.remote_output.rstrip("/")+"/",
        delete=env.rsync_delete
    )


def deploy_git():
    '''for pages service of such as github/gitcafe ...'''
    git_configs = configs.get('git')
    if not isinstance(git_configs, dict):
        git_configs = {}

    with settings(warn_only=True):
        res = local('which -s ghp-import; echo $?', capture=True)
        if int(res.strip()):
            do_exit('Warning: ghp-import not installed! '
                    'run: `pip install ghp-import`')
    output_dir = configs['destination']
    remote = git_configs.get('remote', 'origin')
    branch = git_configs.get('branch', 'gh-pages')
    # commit gh-pages branch and push to remote
    _mesg = 'Update output documentation'
    local('ghp-import -p -m "{0}" -r {1} -b {2} {3}' \
          .format(_mesg, remote, branch, output_dir))


@task
def deploy():
    '''deploy your output to server/git'''
    done = False

    for deploy_type in ('rsync', 'git'):
        if deploy_type in configs:
            func_name = 'deploy_{0}'.format(deploy_type)
            globals()[func_name]()
            done = True

    if not done:
        print(blue('do nothing...'))


@task
def commit():
    '''git commit source changes from all tracked/untracked files'''
    message = 'Update Documentation'
    commit_file = '-A'  # include tracked and untracked files

    with settings(warn_only=True):
        # Changes not staged for commit
        res = local('git status --porcelain 2>/dev/null | grep "^ M" | wc -l',
                    capture=True)
        if int(res.strip()):
            local("git add {0}".format(commit_file))

        # Changes to be committed
        res = local('git status --porcelain 2>/dev/null | grep "^M" | wc -l',
                    capture=True)
        if int(res.strip()):
            local("git commit -m '{0}'".format(message))
