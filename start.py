# all the imports
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, current_app, jsonify
from pybrctl import BridgeController
import netifaces
import subprocess
import atexit

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def _runcmd(cmd, exception):
    """runs a shell command, raises proper exception if it failes"""
    c = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print c.wait()
    if c.wait() != 0:
        raise Exception(exception)
    return c

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
        self.init()
    def getLatency(self):
        return self.latency
    def getVariation(self):
        return self.variation
    def getApprox(self):
        return self.approx
    def getLoss(self):
        return self.loss
    def getCorrelation(self):
        return self.correlation
    def getDuplication(self):
        return self.duplication
    def getCorruption(self):
        return self.corruption
    def init(self):
        _runcmd(["tc", "qdisc", "add", "dev", self.ifname, "root", "netem", "delay", "0ms"], "Could not initialize netem on interface: " + self.ifname)
    def setLatency(self, latency, variation=0, approx=0):
        self.latency = latency
        cmdArr = ["tc", "qdisc", "change", "dev", self.ifname, "root", "netem", "delay", latency + "ms"]
        if (variation != 0 and variation.isnumeric()):
            self.variation = variation
            cmdArr.append(variation + "ms")
            if (approx != 0 and approx.isnumeric()):
                self.approx = approx
                cmdArr.append(approx + "%")
        _runcmd(cmdArr, "Could not set latency " + latency + "ms, variation " + variation + "ms, approximation " + approx + "%% on interface: " + self.ifname)
    def setPacketLoss(self, loss, correlation=0):
        self.loss = loss
        cmdArr = ["tc", "qdisc", "change", "dev", self.ifname, "root", "netem", "loss", loss + "%"]
        if (correlation != 0 and correlation.isnumeric()):
            self.correlation = correlation
            cmdArr.append(correlation + "%")
        _runcmd(cmdArr, "Could not set packet loss " + loss + "%%, correlation " + correlation + "%% on interface: " + self.ifname)
    def setDuplication(self, duplication):
        self.duplication = duplication
        _runcmd(["tc", "qdisc", "change", "dev", self.ifname, "root", "netem", "duplicate", duplication + "%"], "Could not set duplication " + duplication + "%% on interface: " + self.ifname)
    def setCorruption(self, corruption):
        self.corruption = corruption
        _runcmd(["tc", "qdisc", "change", "dev", self.ifname, "root", "netem", "corrupt", corruption + "%"], "Could not set corruption " + corruption + "%% on interface: " + self.ifname)
    def removeAllRules(self):
        self.latency = 0
        self.variation = 0
        self.approx = 0
        self.loss = 0
        self.correlation = 0
        self.duplication = 0
        self.corruption = 0
        _runcmd(["tc", "qdisc", "del", "dev", self.ifname, "root", "netem"], "Could not remove netem rules of interface: " + self.ifname)
    def reInit(self):
        self.removeAllRules()
        self.init()

# single BridgeController Instance
brctl = BridgeController()
br = None
netem = Netem("eth1")

def cleanup():
    netem.removeAllRules()
    brctl.delbr("br0")

def getIfs():
    devs = netifaces.interfaces()
    devs.remove('lo')
    return devs

@app.route('/', methods=['GET'])
def homepage():
    currentBridges = brctl.showall()
    #print currentBridges
    if not currentBridges:
        currentBridges = ["No Bridges currently available!"]
    else:
        pass
    return render_template('index.html', currentBridges=currentBridges)

@app.route('/create', methods=['GET'])
def create():
    return render_template('create.html', devs=getIfs())

@app.route('/create_bridge', methods=['POST'])
def create_bridge():
    global br, brctl
    check = request.form.getlist("check")
    #print check
    br = brctl.addbr("br0")
    for interface in check:
        br.addif(str(interface))
    return redirect(url_for('homepage'))

@app.route('/delete', methods=['GET'])
def delete():
    return render_template('create.html', devs=getIfs())

@app.route('/delete_bridge', methods=['GET'])
def delete_bridge():
    global br, brctl
    brctl.delbr("br0")
    return redirect(url_for('homepage'))

@app.route('/latency', methods=['GET'])
def latency():
    return render_template('latency.html', latency=netem.getLatency(), variation=netem.getVariation(), approx=netem.getApprox())

@app.route('/tc/latency/set', methods=['POST'])
def tc_latency_set():
    latency = request.form["lc"]
    variation = request.form["va"]
    approx = request.form["app"]
    netem.setLatency(latency, variation, approx)
    return render_template('latency.html', latency=netem.getLatency(), variation=netem.getVariation(), approx=netem.getApprox())

@app.route('/tc/latency/reset', methods=['POST'])
def tc_latency_reset():
    netem.reInit()
    return render_template('latency.html', latency=netem.getLatency(), variation=netem.getVariation(), approx=netem.getApprox())

@app.route('/loss', methods=['GET'])
def loss():
    return render_template('loss.html', loss=netem.getLoss(), correlation=netem.getCorrelation())

@app.route('/tc/loss/set', methods=['POST'])
def tc_loss_set():
    loss = request.form["lo"]
    correlation = request.form["co"]
    netem.setPacketLoss(loss, correlation)
    return render_template('loss.html', loss=netem.getLoss(), correlation=netem.getCorrelation())

@app.route('/tc/loss/reset', methods=['POST'])
def tc_loss_reset():
    netem.reInit()
    return render_template('loss.html', loss=netem.getLoss(), correlation=netem.getCorrelation())

@app.route('/duplication', methods=['GET'])
def duplication():
    return render_template('duplication.html', duplication=netem.getDuplication())

@app.route('/tc/duplication/set', methods=['POST'])
def tc_duplication_set():
    duplication = request.form["dup"]
    netem.setDuplication(duplication)
    return render_template('duplication.html', duplication=netem.getDuplication())

@app.route('/tc/duplication/reset', methods=['POST'])
def tc_duplication_reset():
    netem.reInit()
    return render_template('duplication.html', duplication=netem.getDuplication())

@app.route('/corruption', methods=['GET'])
def corruption():
    return render_template('corruption.html', corruption=netem.getCorruption())

@app.route('/tc/corruption/set', methods=['POST'])
def tc_corruption_set():
    corruption = request.form["cor"]
    netem.setCorruption(corruption)
    return render_template('corruption.html', corruption=netem.getCorruption())

@app.route('/tc/corruption/reset', methods=['POST'])
def tc_corruption_reset():
    netem.reInit()
    return render_template('corruption.html', corruption=netem.getCorruption())

if __name__ == "__main__":
    app.run(host='0.0.0.0')

atexit.register(cleanup)
