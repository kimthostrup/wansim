# all the imports
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, current_app, jsonify
from pybrctl import BridgeController
from netem import Netem
import psutil
import netifaces
import atexit

# create our little application :)
app = Flask(__name__)
#app.config['DEBUG'] = True
app.config.from_object(__name__)

# single BridgeController Instance
brctl = BridgeController()
brname = "br0"
br = None
netem = None
bridgeActive = False

def cleanup():
    if netem:
        netem.removeAllRules()
    currentBridges = brctl.showall()
    if currentBridges:
        try:
            brctl.delbr(currentBridges[0])
        except Exception as e:
            print "brctl error: {0}".format(e)

def getIfs():
    devs = netifaces.interfaces()
    devs = [dev for dev in devs if "eth" in dev]
    #print ", ".join(devs)
    return devs

@app.route('/', methods=['GET'])
def homepage():
    currentBridge = brctl.showall()
    statsBridge = None
    if currentBridge:
        currentBridge = currentBridge[0]
        statsBridge = psutil.net_io_counters(True).get(brname)
        print statsBridge
    #print currentBridges
    #if not currentBridges:
    #    currentBridges = ["No Bridges currently available!"]
    #else:
    #    pass
    bridgedIfs = None
    if br:
        bridgedIfs = brctl.getbr(br).getifs()
    return render_template('index.html', currentBridge=currentBridge, bridgedIfs=bridgedIfs, statsBridge=statsBridge)

@app.route('/bridge', methods=['GET'])
def create():
    return render_template('bridge.html', devs=getIfs(), bridgeActive=bridgeActive)

@app.route('/brctl_bridge', methods=['POST'])
def brctl_bridge():
    global br, brctl, bridgeActive
    action = request.form["action"]
    if (action == "set"):
        check = request.form.getlist("check")
        #print check
        br = brctl.addbr(brname)
        for interface in check:
            br.addif(str(interface))
        netem = Netem(brname)
        bridgeActive = True
    elif (action == "reset"):
        brctl.delbr(brname)
        bridgeActive = False
    return redirect(url_for('homepage'))

@app.route('/latency', methods=['GET'])
def latency():
    return render_template('latency.html', latency=netem.getLatency(), variation=netem.getVariation(), approx=netem.getApprox(), bridgeActive=bridgeActive)

@app.route('/tc/latency', methods=['POST'])
def tc_latency():
    action = request.form["action"]
    if (action == "set"):
        latency = request.form["lc"]
        netem.setLatency(latency)
        variation = request.form["va"]
        netem.setVariation(variation)
        approx = request.form["app"]
        netem.setApprox(approx)
        netem.changeQdisc()
    elif (action == "reset"):
        netem.setLatency(0)
        netem.setVariation(0)
        netem.setApprox(0)
        netem.changeQdisc()
    return render_template('latency.html', latency=netem.getLatency(), variation=netem.getVariation(), approx=netem.getApprox(), bridgeActive=bridgeActive)

@app.route('/loss', methods=['GET'])
def loss():
    return render_template('loss.html', loss=netem.getLoss(), correlation=netem.getCorrelation(), bridgeActive=bridgeActive)

@app.route('/tc/loss', methods=['POST'])
def tc_loss():
    action = request.form["action"]
    if (action == "set"):
        loss = request.form["lo"]
        netem.setLoss(loss)
        correlation = request.form["co"]
        netem.setCorrelation(correlation)
        netem.changeQdisc()
    elif (action == "reset"):
        netem.setLoss(0)
        netem.setCorrelation(0)
        netem.changeQdisc()
    return render_template('loss.html', loss=netem.getLoss(), correlation=netem.getCorrelation(), bridgeActive=bridgeActive)

@app.route('/duplication', methods=['GET'])
def duplication():
    return render_template('duplication.html', duplication=netem.getDuplication(), bridgeActive=bridgeActive)

@app.route('/tc/duplication', methods=['POST'])
def tc_duplication():
    action = request.form["action"]
    if (action == "set"):
        duplication = request.form["dup"]
        netem.setDuplication(duplication)
        netem.changeQdisc()
    elif (action == "reset"):
        netem.setDuplication(0)
        netem.changeQdisc()
    return render_template('duplication.html', duplication=netem.getDuplication(), bridgeActive=bridgeActive)

@app.route('/corruption', methods=['GET'])
def corruption():
    return render_template('corruption.html', corruption=netem.getCorruption(), bridgeActive=bridgeActive)

@app.route('/tc/corruption', methods=['POST'])
def tc_corruption():
    action = request.form["action"]
    if (action == "set"):
        corruption = request.form["cor"]
        netem.setCorruption(corruption)
        netem.changeQdisc()
    elif (action == "reset"):
        netem.setCorruption(0)
        netem.changeQdisc()
    return render_template('corruption.html', corruption=netem.getCorruption(), bridgeActive=bridgeActive)

@app.route('/tc/reset', methods=['GET'])
def tc_reset():
    netem.reInit()
    return redirect(url_for('homepage'))


if __name__ == "__main__":
    cleanup()
    app.run(host='0.0.0.0')

atexit.register(cleanup)
