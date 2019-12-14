import logging
from config import config
from twilio.rest import Client
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors, discovery
from email.mime.text import MIMEText
import base64
from pytz import timezone

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

bodyText = 'Title: {} \nPrice: {} \nTimestamp: {} \nLink: {}'
bodyTextHTML = '<p style="font-size:16px"><strong>Title: </strong> {} <br><strong>Price: </strong>{} <br><strong>Timestamp: </strong>{} <br><strong>Link: </strong>{}</p>'


class Notifications:
	def __init__(self):
		logger.debug('Notifications starting')
		self.smsclient = Client(config.account_sid, config.auth_token)
		self.service = self.connectGmail()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		logger.debug('Closing notifications')

	def connectGmail(self):
		logger.debug('Connecting to Gmail')
		creds = None
		if os.path.exists('token.pickle'):
			with open('token.pickle', 'rb') as token:
				creds = pickle.load(token)
		# If there are no (valid) credentials available, let the user log in.
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					config.settings['gmail-credentials'], SCOPES)
				creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open('token.pickle', 'wb') as token:
				pickle.dump(creds, token)
		service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
		logger.debug('Gmail connected')
		return service

	def createEmailMessage(self, subject, message_text):
		logger.debug('Creating message')
		message = MIMEText(message_text, 'html')
		message['to'] = config.settings['email-receiver']
		message['from'] = config.settings['email-sender']
		message['subject'] = subject
		return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

	def sendEmail(self, content):
		timestamp = content[1]['timestamp'].astimezone(timezone('Australia/Sydney')).strftime('%d/%m/%Y %H:%M:%S')
		subject = 'Ozbargain-scraper: An item matching "{}" has been posted'.format(content[0])
		message_text = bodyTextHTML.format(content[1]['title'], content[1]['price'], timestamp,  content[1]['link'])
		message = self.createEmailMessage(subject, message_text)
		logger.debug('Sending email')
		try:
			message = (self.service.users().messages().send(userId="me", body=message).execute())
			logger.debug('Email sent. message ID: %s', message['id'])
			return message
		except errors.HttpError as error:
			logger.error('An error occurred', exc_info=True)
		

	def sendSMS(self, content):
		logger.debug('Sending sms')
		timestamp = content[1]['timestamp'].astimezone(timezone('Australia/Sydney')).strftime('%d/%m/%Y %H:%M:%S')
		messageText = 'An item matching "{}" was posted. \n\n'.format(content[0]) + bodyText.format( content[1]['title'], content[1]['price'], timestamp, content[1]['link'])
		message = self.smsclient.messages.create(
			body=messageText,
			from_='+14843010951',
			to='+61478790532'
		)
		logger.debug('sms sent')
