// Example React component (ContactsList.js)
import React, { useState, useEffect } from 'react';

function ContactsList() {
  const [contacts, setContacts] = useState([]);

  useEffect(() => {
    fetch('/contacts')
      .then(response => response.json())
      .then(data => setContacts(data));
  }, []);

  const initiateConversation = (contact, channel) => {
    fetch('/trigger_conversation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contactId: contact.id,
        channel: channel,
        phoneNumber: contact.msisdn, // or other relevant channel ID
      }),
    });
  };

  return (
    <div>
      <h2>Contacts</h2>
      <ul>
        {contacts.map(contact => (
          <li key={contact.id}>
            {contact.name} - {contact.msisdn}
            <button onClick={() => initiateConversation(contact, 'sms')}>SMS</button>
            <button onClick={() => initiateConversation(contact, 'whatsapp')}>WhatsApp</button>
          </li>
        ))}
      </ul>
      {/* Add forms for CRUD operations */}
    </div>
  );
}

export default ContactsList;
