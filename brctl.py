import subprocess

def _runcmd(cmd, exception):
    c = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if c.wait() != 0:
        raise BrctlException(exception)
    return c


test = _runcmd(["ls", "-l", "/etc/resolv.conf"], "ls exception")
print (test.stdout.read())
