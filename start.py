# all the imports
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, current_app, jsonify
from pybrctl import BridgeController
import netifaces

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# single BridgeController Instance
brctl = BridgeController()
br = None

def getIfs():
    devs = netifaces.interfaces()
    devs.remove('lo')
    return devs

@app.route('/', methods=['GET'])
def homepage():
    currentBridges = brctl.showall()
    print currentBridges
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



if __name__ == "__main__":
    app.run(host='0.0.0.0')
