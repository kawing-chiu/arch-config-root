import pwd
import subprocess
import os
from multiprocessing import Process


def get_user_info(user_name):
    user_record = pwd.getpwnam(user_name)
    user_home = user_record.pw_dir
    uid = user_record.pw_uid
    gid = user_record.pw_gid
    return uid, gid, user_home

def _change_user(uid, gid):
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)

def call_f_as_user(user_name, f, args=(), kwargs={}, cwd=None):
    """Call function as another user.

    By default, cwd is set to the home dir of the 
    run-as user.
    """
    if os.geteuid() != 0:
        raise OSError("You're not root, cannot run "
                "function as other user.")
    uid, gid, user_home = get_user_info(user_name)

    if cwd is not None:
        cwd = os.path.abspath(cwd)

    def _f():
        _change_user(uid, gid)
        os.environ['HOME'] = user_home
        os.environ['LOGNAME'] = user_name
        os.environ['USER'] = user_name
        if cwd is not None:
            os.chdir(cwd)
            os.environ['PWD'] = cwd
        else:
            os.chdir(user_home)
            os.environ['PWD'] = user_home
        f(*args, **kwargs)

    p = Process(target=_f)
    p.start()
    p.join()

def run_as_user(user_name, cmd, cwd=None, **kwargs):
    """Run command as another user.

    By default, cwd is set to the home dir of the 
    run-as user.
    """
    if os.geteuid() != 0:
        raise OSError("You're not root, cannot run "
                "program as other user.")
    uid, gid, user_home = get_user_info(user_name)

    env = kwargs.pop('env', None)
    if env is None:
        env = os.environ.copy()
    env['HOME'] = user_home
    env['LOGNAME'] = user_name
    env['USER'] = user_name
    if cwd is None:
        cwd = user_home
        env['PWD'] = user_home
    else:
        cwd = os.path.abspath(cwd)
        env['PWD'] = cwd

    def _preexec():
        _change_user(uid, gid)

    subprocess.check_call(cmd, cwd=cwd, env=env,
        preexec_fn=_preexec, **kwargs)

def run(*args, **kwargs):
    subprocess.check_call(*args, **kwargs)

