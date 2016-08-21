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
            # install root CBQ
            _runcmd(["tc", "qdisc", "add", "dev", self.ifname, "root", "handle", "1:", "cbq", "avpkt", "1000", "bandwidth", "10mbit"])

            # shape everything at $USPEED speed - this prevents huge queues in your
            # DSL modem which destroy latency
            _runcmd(["tc", "class", "add", "dev", self.ifname, "parent", "1:", "classid", "1:1", "cbq",
                "rate", str(self.up) + "kbit", "allot", "1500", "prio", "5", "bounded", "isolated"])

            # high prio class 1:10:
            _runcmd(["tc", "class", "add", "dev", self.ifname, "parent", "1:1", "classid", "1:10", "cbq",
                "rate", str(self.up) + "kbit", "allot", "1600", "prio", "1", "avpkt", "1000"])

            # bulk and default class 1:20 - gets slightly less traffic,
            #  and a lower priority:
            _runcmd(["tc", "class", "add", "dev", self.ifname, "parent", "1:1", "classid", "1:20", "cbq",
                "rate", str(9*self.up/10) + "kbit", "allot", "1600", "prio", "2", "avpkt", "1000"])

            # add netem modifiers to high prio and default
            highprioArr = ["tc", "qdisc", "add", "dev", self.ifname, "parent", "1:10", "handle", "10:"]
            highprioArr.extend(netemArr)
            _runcmd(highprioArr, "Could not apply changes on interface: " + self.ifname + "\ncommand: " + " ".join(highprioArr))
            defaultArr = ["tc", "qdisc", "add", "dev", self.ifname, "parent", "1:20", "handle", "20:"]
            defaultArr.extend(netemArr)
            _runcmd(defaultArr, "Could not apply changes on interface: " + self.ifname + "\ncommand: " + " ".join(defaultArr))

            # start filters
            # TOS Minimum Delay (ssh, NOT scp) in 1:10:
            _runcmd(["tc", "filter", "add", "dev", self.ifname, "parent", "1:",
                "protocol", "ip", "prio", "10", "u32", "match", "ip", "tos", "0x10", "0xff", "flowid", "1:10"])
            # ICMP (ip protocol 1)
            _runcmd(["tc", "filter", "add", "dev", self.ifname, "parent", "1:",
                "protocol", "ip", "prio", "11", "u32", "match", "ip", "protocol", "1", "0xff", "flowid", "1:10"])
            # prioritize small packets (<64 bytes)
            _runcmd(["tc", "filter", "add", "dev", self.ifname, "parent", "1:",
                "protocol", "ip", "prio", "12", "u32",
                    "match", "ip", "protocol", "6", "0xff",
                    "match", "u8", "0x05", "0x0f", "at", "0",
                    "match", "u16", "0x0000", "0xffc0", "at", "2",
                "flowid", "1:10"])
            # default ends up here
            _runcmd(["tc", "filter", "add", "dev", self.ifname, "parent", "1:",
                "protocol", "ip", "prio", "18", "u32", "match", "ip", "dst", "0.0.0.0/0", "flowid", "1:20"])
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
                "protocol", "ip", "prio", "50", "u32", "match", "ip", "src", "0.0.0.0/0", "police", "rate", str(self.down) + "kbit", "burst", "10k", "drop", "flowid", ":1"])

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
