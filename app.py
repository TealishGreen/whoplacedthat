import os
from dataclasses import dataclass
from flask import Flask, jsonify, request, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import DeclarativeMeta

import uuid
import json

actions = ["Place_Block", "Break_Block", "Place_BlockWE", "Break_BlockWE", "Debug_Stick", "Container_Add", "Container_Remove"]

reverseActions = ["Break_Block", "Place_Block", "Break_BlockWE", "Place_BlockWE", "Debug_Stick", "Container_Remove", "Container_Add"]

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = "67yu7uy6h j7"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  

db = SQLAlchemy(app)

# Source - https://stackoverflow.com/a
# Posted by Sasha B, modified by community. See post 'Timeline' for change history
# Retrieved 2026-01-05, License - CC BY-SA 4.0

# Modified by TealishGreen

class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                        if isinstance(data, datetime):
                            json.dumps(data.timestamp())
                            fields[field] = data.timestamp()
                        else:
                            fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

@dataclass
class Block(db.Model):
    locationX = db.Column(db.Integer, nullable=False)
    locationY = db.Column(db.Integer, nullable=False)
    locationZ = db.Column(db.Integer, nullable=False)
    material = db.Column(db.String(50), nullable=False)
    state = db.Column(db.Text, nullable=False)
    modifier = db.Column(db.String(36), nullable=False)
    action = db.Column(db.String(15), nullable=False)
    modifiedAt = db.Column(db.DateTime(timezone=False),
                           server_default=func.now())
    id = db.Column(db.String(30), primary_key=True)

    def __repr__(self):
        return f'<Block {self.locationX} {self.locationY} {self.locationZ} {self.modifier} {self.modifiedAt} {self.id}>'
    
    
@app.route('/')
def index():
    return "y'all need to stop with this softcoding stuff: You're generally referring to removing repeated code – and yes, this a good thing, normally. However, there are two issues with the attitude around this. First, not every situation mandates this kind of code structure. This is especially true of smaller games made by newer developers. We shouldn't avoid adding certain QOL features simply because in a \"properly\" coded game it isn't necessary. This second point doesn't apply specifically to this conversation but I see it coming up frequently so here goes: a lot of people take this way too far. I have seen so many plots where they do crazy things like spawn items on the ground to load information and whatnot. This is not good. Don't sacrifice code legibility and efficiency simply because they believe it makes coding experience easier. There is a delicate balance between well designed, easy to maintain, and efficient code. Softcoding is not always the way to achieve this balance. So please, just think about the systems you're designing and whether or not anything is actually improved. tl;dr elitism through \"better practice\" / softcoding doesn't help, and often it isn't the right answer"

@app.route('/version/')
def version():
    return jsonify({version: "2.0"})

@app.route('/get/<int:x>|<int:y>|<int:z>/')
def student(x, y, z):
    student = Block.query.filter(Block.locationX == x, Block.locationY == y, Block.locationZ == z)
    student = student[0]
    return json.dumps({'success':True}), 200, jsonify({"modifier": student.modifier, "date": student.modifiedAt}), {'ContentType':'application/json'}

@app.route('/getbefore/<int:date>')
def getbefore(date):
    blocks = Block.query.filter(Block.modifiedAt <= datetime.utcfromtimestamp(date)).all()
    print(blocks)
    return Response(json.dumps(blocks, cls=AlchemyEncoder), mimetype='application/json')

@app.route('/getrollbackdata/<int:date>|<modifier>', methods=("GET"))
def getafter(date, modifier):
    blocks = json.dumps(Block.filter(Block.modifiedAt >= datetime.utcfromtimestamp(date), Block.modifier == modifier), cls=AlchemyEncoder)
    db.session.commit()
    return Response(blocks, mimetype='application/json')

@app.route('/delrollbackdata/<int:date>|<modifier>', methods=("DELETE"))
def getafter(date, modifier):
    blocks = json.dumps(Block.filter(Block.modifiedAt >= datetime.utcfromtimestamp(date), Block.modifier == modifier), cls=AlchemyEncoder)
    db.session.execute(
        db.delete(Block).filter(Block.modifiedAt >= datetime.utcfromtimestamp(date), Block.modifier == modifier)
    )
    db.session.commit()
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/deleteold', methods=('DELETE'))
def deleteold():
    db.session.execute(
        db.delete(Block).filter(Block.modifiedAt <= date.today() - timedelta(20))
    )
    db.session.commit()
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/create/<x>|<y>|<z>|<material>|<state>|<modifier>|<int:action>|<date>/', methods=('POST'))
def create(x, y, z, material, state, modifier, action, date):
    id = str(uuid.uuid4())
    x = int(x)
    y = int(y)
    z = int(z)
    action = actions[action]
    date = datetime.utcfromtimestamp(float(date))
    student = Block(locationX=x, locationY=y, locationZ=z, material=material, state=state, modifier=modifier, action=action, modifiedAt=date, id=id)
    db.session.add(student)
    db.session.commit()
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route("/checkconn")
def checkConn():
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}