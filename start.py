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
    def __init__(self, ifname):
        self.ifname = ifname
        self.init()
    def init(self):
        _runcmd(["tc", "qdisc", "add", "dev", self.ifname, "root", "netem", "delay", "0ms"], "Could not initialize netem on interface: " + self.ifname)
    def setLatency(self, delay, variation=0, approx=0):
        cmdArr = ["tc", "qdisc", "change", "dev", self.ifname, "root", "netem", "delay", delay + "ms"]
        if (variation != 0):
            cmdArr.append(variation + "ms")
            if (approx != 0):
                cmdArr.append(approx + "%")
        _runcmd(cmdArr, "Could not set latency " + delay + "ms, variation " + variation + "ms, approximation " + approx + "%% on interface: " + self.ifname)
    def removeRules(self):
        _runcmd(["tc", "qdisc", "del", "dev", self.ifname, "root", "netem"], "Could not remove netem rules of interface: " + self.ifname)
    def reInit(self):
        self.removeRules()
        self.init()

# single BridgeController Instance
brctl = BridgeController()
br = None
netem = Netem("eth1")

def cleanup():
    netem.removeRules()
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
    print check

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

@app.route('/slider', methods=['GET'])
def slider():
    return render_template('slider.html')

@app.route('/tc/latency/set', methods=['POST'])
def tc_latency_set():
    latency = request.form["lc"]
    variation = request.form["va"]
    approx = request.form["app"]
    netem.setLatency(latency, variation, approx)
    return render_template('slider.html')

@app.route('/tc/latency/reset', methods=['POST'])
def tc_latency_reset():
    netem.reInit()
    return render_template('slider.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')

atexit.register(cleanup)
