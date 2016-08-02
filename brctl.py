import subprocess

def _runcmd(cmd, exception):
    """runs a shell command, raises proper exception if it failes"""
    c = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print c.wait()
    if c.wait() != 0:
        raise BrctlException(exception)
    return c


test = _runcmd(["ls", "-l", "/etc/resolv.conf"], "ls exception")
print (test.stdout.read())
