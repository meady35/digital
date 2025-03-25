# app.py (Flask backend)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///contacts.db') # Use environment variable or default to sqlite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)  # Enable CORS for Webex App frontend

WEBEX_CONNECT_WEBHOOK_URL = os.environ.get('WEBEX_CONNECT_WEBHOOK_URL') #Webex Connect webhook URL

# Database Models
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    msisdn = db.Column(db.String(20)) # Phone number for SMS/WhatsApp

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'msisdn': self.msisdn
        }

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customerChannel = db.Column(db.String(50)) # e.g., 'sms', 'whatsapp'
    customerChannelId = db.Column(db.String(255)) # e.g., phone number
    collabAgentId = db.Column(db.String(255))
    collabGuestId = db.Column(db.String(255))
    collabExtra1 = db.Column(db.String(255))
    collabExtra2 = db.Column(db.String(255))
    collabExtra3 = db.Column(db.String(255))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    contact = db.relationship('Contact', backref=db.backref('sessions', lazy=True))

    def to_dict(self):
        contact_data = self.contact.to_dict() if self.contact else None
        return {
            'id': self.id,
            'customerChannel': self.customerChannel,
            'customerChannelId': self.customerChannelId,
            'collabAgentId': self.collabAgentId,
            'collabGuestId': self.collabGuestId,
            'collabExtra1': self.collabExtra1,
            'collabExtra2': self.collabExtra2,
            'collabExtra3': self.collabExtra3,
            'contact': contact_data
        }

with app.app_context():
    db.create_all()

# Contact CRUD API
@app.route('/contacts', methods=['GET', 'POST'])
def handle_contacts():
    if request.method == 'GET':
        contacts = Contact.query.all()
        return jsonify([contact.to_dict() for contact in contacts])
    elif request.method == 'POST':
        data = request.get_json()
        new_contact = Contact(name=data['name'], msisdn=data.get('msisdn'))
        db.session.add(new_contact)
        db.session.commit()
        return jsonify(new_contact.to_dict()), 201

@app.route('/contacts/<int:contact_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if request.method == 'GET':
        return jsonify(contact.to_dict())
    elif request.method == 'PUT':
        data = request.get_json()
        contact.name = data['name']
        contact.msisdn = data.get('msisdn', contact.msisdn)
        db.session.commit()
        return jsonify(contact.to_dict())
    elif request.method == 'DELETE':
        db.session.delete(contact)
        db.session.commit()
        return '', 204

# Session CRUD API
@app.route('/sessions', methods=['GET', 'POST'])
def handle_sessions():
    if request.method == 'GET':
        sessions = Session.query.all()
        return jsonify([session.to_dict() for session in sessions])
    elif request.method == 'POST':
        data = request.get_json()
        contact = Contact.query.get(data.get('contact_id'))
        new_session = Session(
            customerChannel=data['customerChannel'],
            customerChannelId=data['customerChannelId'],
            collabAgentId=data.get('collabAgentId'),
            collabGuestId=data.get('collabGuestId'),
            collabExtra1=data.get('collabExtra1'),
            collabExtra2=data.get('collabExtra2'),
            collabExtra3=data.get('collabExtra3'),
            contact=contact
        )
        db.session.add(new_session)
        db.session.commit()
        return jsonify(new_session.to_dict()), 201

@app.route('/sessions/<int:session_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_session(session_id):
    session = Session.query.get_or_404(session_id)
    if request.method == 'GET':
        return jsonify(session.to_dict())
    elif request.method == 'PUT':
        data = request.get_json()
        session.customerChannel = data['customerChannel']
        session.customerChannelId = data['customerChannelId']
        session.collabAgentId = data.get('collabAgentId', session.collabAgentId)
        session.collabGuestId = data.get('collabGuestId', session.collabGuestId)
        session.collabExtra1 = data.get('collabExtra1', session.collabExtra1)
        session.collabExtra2 = data.get('collabExtra2', session.collabExtra2)
        session.collabExtra3 = data.get('collabExtra3', session.collabExtra3)
        if 'contact_id' in data:
           session.contact_id = data['contact_id']
        db.session.commit()
        return jsonify(session.to_dict())
    elif request.method == 'DELETE':
        db.session.delete(session)
        db.session.commit()
        return '', 204

# Webex Connect Webhook Trigger
@app.route('/trigger_conversation', methods=['POST'])
def trigger_conversation():
    data = request.get_json()
    try:
        response = requests.post(WEBEX_CONNECT_WEBHOOK_URL, json=data)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return jsonify({'message': 'Conversation trigger successful'}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) # Set debug to False for production
