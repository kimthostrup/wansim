import subprocess

# runs a command(cmd expected as array) in the shell, raises Exception if command fails
def _runcmd(cmd, exception=""):
    """runs a shell command, raises proper exception if it failes"""
    c = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if c.wait() != 0:
        stdout = c.communicate()[0]
        #print 'STDOUT:{}'.format(stdout)
        raise Exception(exception)
    return c

# Tc Class to manipulate a network connection
class Tc(object):
    def __init__(self, ifname, down=0, up=0, delay=0, jitter=0, delcorr=0, loss=0, losscorr=0, duplication=0, dcorr=0, corruption=0, ccorr=0):
        self.ifname = ifname
        self.down = down
        self.up = up
        self.delay = delay
        self.jitter = jitter
        self.delcorr = delcorr
        self.loss = loss
        self.losscorr = losscorr
        self.duplication = duplication
        self.dcorr = dcorr
        self.corruption = corruption
        self.ccorr = ccorr
    def getIfName(self):
        return self.ifname
    def getDown(self):
        return self.down
    def setDown(self, down):
        self.down = down
    def getUp(self):
        return self.up
    def setUp(self, up):
        self.up = up
    def getDelay(self):
        return self.delay
    def setDelay(self, delay):
        self.delay = delay
    def getJitter(self):
        return self.jitter
    def setJitter(self, jitter):
        self.jitter = jitter
    def getDelCorr(self):
        return self.delcorr
    def setDelCorr(self, delcorr):
        self.delcorr = delcorr
    def getLoss(self):
        return self.loss
    def setLoss(self, loss):
        self.loss = loss
    def getLossCorr(self):
        return self.losscorr
    def setLossCorr(self, losscorr):
        self.losscorr = losscorr
    def getDuplication(self):
        return self.duplication
    def setDuplication(self, duplication):
        self.duplication = duplication
    def getDCorr(self):
        return self.dcorr
    def setDCorr(self, dcorr):
        self.dcorr = dcorr
    def getCorruption(self):
        return self.corruption
    def setCorruption(self, corruption):
        self.corruption = corruption
    def getCCorr(self):
        return self.ccorr
    def setCCorr(self, ccorr):
        self.ccorr = ccorr
    def changeTc(self):
        self.resetTc()

        netemArr = [
            "netem",
            "delay", str(self.delay) + "ms", str(self.jitter) + "ms", str(self.delcorr) + "%",
            "loss", str(self.loss) + "%", str(self.losscorr) + "%",
            "duplicate", str(self.duplication) + "%", str(self.dcorr) + "%",
            "corrupt", str(self.corruption) + "%", str(self.ccorr) + "%"
        ]


        if (self.up is not 0) :
            _runcmd(["tc", "qdisc", "add", "dev", self.ifname, "root", "handle", "1:", "htb"])

            _runcmd(["tc", "class", "add", "dev", self.ifname, "parent", "1:", "classid", "1:1", "htb",
                "rate", str(self.up) + "kbit"])

            _runcmd(["tc", "class", "add", "dev", self.ifname, "parent", "1:1", "classid", "1:11", "htb",
                "rate", str(self.up) + "kbit"])

            # add netem modifiers
            addNetem = ["tc", "qdisc", "add", "dev", self.ifname, "parent", "1:11", "handle", "10:"]
            addNetem.extend(netemArr)
            _runcmd(addNetem, "Could not apply changes on interface: " + self.ifname + "\ncommand: " + " ".join(addNetem))

            # start filter
            _runcmd(["tc", "filter", "add", "dev", self.ifname, "parent", "1:",
                "protocol", "ip", "prio", "1", "u32", "match", "ip", "dst", "0.0.0.0/0", "flowid", "1:11"])
        else:
            # prepare command array
            cmdArr = [
                "tc", "qdisc", "add", "dev", str(self.ifname), "root"
            ]
            cmdArr.extend(netemArr)
            _runcmd(cmdArr, "Could not apply changes on interface: " + self.ifname + "\ncommand: " + " ".join(cmdArr))

        if (self.down is not 0):
            _runcmd(["tc", "qdisc", "add", "dev", self.ifname, "handle", "ffff:", "ingress"])

            # filter *everything* to it (0.0.0.0/0), drop everything that's
            # coming in too fast:
            _runcmd(["tc", "filter", "add", "dev", self.ifname, "parent", "ffff:",
                "protocol", "ip", "prio", "1", "u32", "match", "ip", "src", "0.0.0.0/0", "police", "rate", str(self.down) + "kbit", "burst", "10k", "drop", "flowid", ":1"])

    # resets all rules
    def removeAllRules(self):
        self.down = 0
        self.up = 0
        self.delay = 0
        self.jitter = 0
        self.delcorr = 0
        self.loss = 0
        self.losscorr = 0
        self.duplication = 0
        self.dcorr = 0
        self.corruption = 0
        self.ccorr = 0
    # reset tc on interface
    def resetTc(self):
        try:
            _runcmd(["tc", "qdisc", "del", "dev", self.ifname, "root"])
        except Exception as e:
            pass
        try:
            _runcmd(["tc", "qdisc", "del", "dev", self.ifname, "ingress"])
        except Exception as e:
            pass
