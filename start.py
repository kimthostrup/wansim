# all the imports
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, current_app, jsonify
from flask_script import Manager
from pybrctl import BridgeController
from tc import Tc
import psutil
import netifaces
import atexit

# create our little application
app = Flask(__name__)
app.config.from_object(__name__)

#create manager
manager = Manager(app)

# single BridgeController Instance
brctl = BridgeController()
brname = "br0"          # name of the to be bridge
br = None               # the bridge object created from the bridge controller
tc = Tc("lo")     # default init to loopback device
bridgeActive = False    # flag if bridge is active

################ HELPERS ################

# cleanup configurations on startup and exit
def cleanup():
    try:
        tc.removeAllRules()
        tc.resetTc()
    except Exception as e:
        print "tc error/potentially nothing to do: {0}".format(e)

    currentBridges = brctl.showall()
    if currentBridges:
        try:
            brctl.delbr(currentBridges[0])
        except Exception as e:
            print "brctl error/potentially nothing to do: {0}".format(e)

# helper to get all cable interface names (eth0, eth1, etc.)
def getIfs():
    devs = netifaces.interfaces()
    devs = [dev for dev in devs if "eth" in dev]
    #print ", ".join(devs)
    return devs

################ ROUTING ################

# main entry of the webinterface
@app.route('/', methods=['GET'])
def homepage():
    currentBridge = brctl.showall()
    statsBridge = None
    if currentBridge:
        currentBridge = currentBridge[0]
        statsBridge = psutil.net_io_counters(True).get(br.getifs()[-1])
        print statsBridge
    bridgedIfs = None
    if br:
        bridgedIfs = br.getifs()
    return render_template('index.html', currentBridge=currentBridge, bridgedIfs=bridgedIfs, statsBridge=statsBridge)

# route to bridge creation
@app.route('/bridge', methods=['GET'])
def create():
    return render_template('bridge.html', devs=getIfs(), bridgeActive=bridgeActive)

# route to create a bridge with given interfaces
@app.route('/brctl_bridge', methods=['POST'])
def brctl_bridge():
    global br, brctl, bridgeActive, tc
    action = request.form["action"]
    if (action == "set"):
        check = request.form.getlist("check")
        #print check
        br = brctl.addbr(brname)
        for interface in check:
            br.addif(str(interface))
        tc = Tc(br.getifs()[0])
        bridgeActive = True
    elif (action == "reset"):
        brctl.delbr(brname)
        bridgeActive = False
    return redirect(url_for('homepage'))

# route to up/downn speed settings
@app.route('/speed', methods=['GET'])
def speed():
    return render_template('speed.html', up=tc.getUp(), down=tc.getDown(), bridgeActive=bridgeActive)

# route to apply given up/down speed settings on the bridge
@app.route('/tc/speed', methods=['POST'])
def tc_speed():
    action = request.form["action"]
    if (action == "set"):
        down = request.form["down"]
        tc.setDown(int(down))
        up = request.form["up"]
        tc.setUp(int(up))
	print "down:" + str(down) + ", up:" + str(up)
        tc.changeTc()
    elif (action == "reset"):
        tc.setDown(0)
        tc.setUp(0)
        tc.changeTc()
    return render_template('speed.html', up=tc.getUp(), down=tc.getDown(), bridgeActive=bridgeActive)

# route to latency settings
@app.route('/latency', methods=['GET'])
def latency():
    return render_template('latency.html', delay=tc.getDelay(), jitter=tc.getJitter(), delcorr=tc.getDelCorr(), bridgeActive=bridgeActive)

# route to apply given latency settings on the bridge
@app.route('/tc/latency', methods=['POST'])
def tc_latency():
    action = request.form["action"]
    if (action == "set"):
        delay = request.form["lc"]
        tc.setDelay(delay)
        jitter = request.form["va"]
        tc.setJitter(jitter)
        delcorr = request.form["app"]
        tc.setDelCorr(delcorr)
        tc.changeTc()
    elif (action == "reset"):
        tc.setDelay(0)
        tc.setJitter(0)
        tc.setDelCorr(0)
        tc.changeTc()
    return render_template('latency.html', delay=tc.getDelay(), jitter=tc.getJitter(), delcorr=tc.getDelCorr(), bridgeActive=bridgeActive)

# route to packet loss settings
@app.route('/loss', methods=['GET'])
def loss():
    return render_template('loss.html', loss=tc.getLoss(), losscorr=tc.getLossCorr(), bridgeActive=bridgeActive)

# route to apply given packet loss settings on the bridge
@app.route('/tc/loss', methods=['POST'])
def tc_loss():
    action = request.form["action"]
    if (action == "set"):
        loss = request.form["lo"]
        tc.setLoss(loss)
        losscorr = request.form["co"]
        tc.setLossCorr(losscorr)
        tc.changeTc()
    elif (action == "reset"):
        tc.setLoss(0)
        tc.setLossCorr(0)
        tc.changeTc()
    return render_template('loss.html', loss=tc.getLoss(), losscorr=tc.getLossCorr(), bridgeActive=bridgeActive)

# route to packet duplication settings
@app.route('/duplication', methods=['GET'])
def duplication():
    return render_template('duplication.html', duplication=tc.getDuplication(), dcorr=tc.getDCorr(), bridgeActive=bridgeActive)

# route to apply given packet duplication settings on the bridge
@app.route('/tc/duplication', methods=['POST'])
def tc_duplication():
    action = request.form["action"]
    if (action == "set"):
        duplication = request.form["dup"]
        tc.setDuplication(duplication)
        dcorr = request.form["dcorr"]
        tc.setDCorr(dcorr)
        tc.changeTc()
    elif (action == "reset"):
        tc.setDuplication(0)
        tc.setDCorr(0)
        tc.changeTc()
    return render_template('duplication.html', duplication=tc.getDuplication(), dcorr=tc.getDCorr(), bridgeActive=bridgeActive)

# route to packet corruption settings
@app.route('/corruption', methods=['GET'])
def corruption():
    return render_template('corruption.html', corruption=tc.getCorruption(), ccorr=tc.getCCorr(), bridgeActive=bridgeActive)

# route to apply given packet corruption settings on the bridge
@app.route('/tc/corruption', methods=['POST'])
def tc_corruption():
    action = request.form["action"]
    if (action == "set"):
        corruption = request.form["cor"]
        tc.setCorruption(corruption)
        ccorr = request.form["ccorr"]
        tc.setCCorr(ccorr)
        tc.changeTc()
    elif (action == "reset"):
        tc.setCorruption(0)
        tc.setCCorr(0)
        tc.changeTc()
    return render_template('corruption.html', corruption=tc.getCorruption(), ccorr=tc.getCCorr(), bridgeActive=bridgeActive)

# route to reset all settings, bridged will reamin active
@app.route('/tc/reset', methods=['GET'])
def tc_reset():
    tc.reInit()
    return redirect(url_for('homepage'))

################ MANAGER ################

# cleans up network configuration if necessary before starting up the webservice
@manager.command
def runserver():
    # register cleanup function atexit of program
    atexit.register(cleanup)
    cleanup()
    app.run(host='0.0.0.0')	#starts flask webservice

#this is executed when the file is started with python
#it starts up the manager and the manager checks for extra parameters
#available paramaters:
#   runserver   #will start the flask webserver
if __name__ == "__main__":
    manager.run()
