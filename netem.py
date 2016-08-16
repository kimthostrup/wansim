import subprocess

# runs a command(cmd expected as array) in the shell, raises Exception if command fails
def _runcmd(cmd, exception):
    """runs a shell command, raises proper exception if it failes"""
    c = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if c.wait() != 0:
        stdout = c.communicate()[0]
        print 'STDOUT:{}'.format(stdout)
        raise Exception(exception)
    return c

# Netem Class to manipulate a network connection
class Netem(object):
    def __init__(self, ifname, latency=0, variation=0, approx=0, loss=0, correlation=0, duplication=0, corruption=0):
        self.ifname = ifname
        self.latency = latency
        self.variation = variation
        self.approx = approx
        self.loss = loss
        self.correlation = correlation
        self.duplication = duplication
        self.corruption = corruption
        #self.init()
    def getIfName(self):
        return self.ifname
    def getLatency(self):
        return self.latency
    def setLatency(self, latency):
        self.latency = latency
    def getVariation(self):
        return self.variation
    def setVariation(self, variation):
        self.variation = variation
    def getApprox(self):
        return self.approx
    def setApprox(self, approx):
        self.approx = approx
    def getLoss(self):
        return self.loss
    def setLoss(self, loss):
        self.loss = loss
    def getCorrelation(self):
        return self.correlation
    def setCorrelation(self, correlation):
        self.correlation = correlation
    def getDuplication(self):
        return self.duplication
    def setDuplication(self, duplication):
        self.duplication = duplication
    def getCorruption(self):
        return self.corruption
    def setCorruption(self, corruption):
        self.corruption = corruption
    # init, has to be run once after initialisation
    def init(self):
        _runcmd(["tc", "qdisc", "add", "dev", self.ifname, "root", "netem", "delay", "0ms"], "Could not initialize netem on interface: " + self.ifname)
    # after the init, every setting set with set functions can be applied with changeQdisc
    def changeQdisc(self):
        cmdArr = [
            "tc", "qdisc", "change", "dev", str(self.ifname), "root", "netem",
            "delay", str(self.latency) + "ms", str(self.variation) + "ms", str(self.approx) + "%",
            "loss", str(self.loss) + "%", str(self.correlation) + "%",
            "duplicate", str(self.duplication) + "%",
            "corrupt", str(self.corruption) + "%"
        ]
        _runcmd(cmdArr, "Could not apply changes on interface: " + self.ifname + "\ncommand: " + " ".join(cmdArr))
    # resets all rules and removes them in the shell
    def removeAllRules(self):
        self.latency = 0
        self.variation = 0
        self.approx = 0
        self.loss = 0
        self.correlation = 0
        self.duplication = 0
        self.corruption = 0
        _runcmd(["tc", "qdisc", "del", "dev", self.ifname, "root", "netem"], "Could not remove netem rules of interface: " + self.ifname)
    # complete re-initialisation
    def reInit(self):
        self.removeAllRules()
        self.init()
