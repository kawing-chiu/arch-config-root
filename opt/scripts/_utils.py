import pwd
import subprocess
import os

def run_as_user(user, cmd, cwd=None, **kwargs):
    """Run command as another user.

    By default, cwd is set to the home dir of the 
    run-as user.
    """
    if os.geteuid() != 0:
        raise OSError("You're not root, cannot run "
                "program as other user.")
    user_record = pwd.getpwnam(user)
    user_name = user_record.pw_name
    user_home = user_record.pw_dir
    uid = user_record.pw_uid
    gid = user_record.pw_gid

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

    def change_user():
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)

    subprocess.call(cmd, cwd=cwd, env=env,
        preexec_fn=change_user, **kwargs)

def run(*args, **kwargs):
    subprocess.call(*args, **kwargs)

