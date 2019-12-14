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

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class Notifications:
	def __init__(self):
		logger.debug('Notifications starting')
		self.smsMessage = '\nAn item from you list was posted. \n\nTitle: {} \nPrice: {} \nTimestamp: {} \nLink: {}'
		self.smsclient = Client(config.account_sid, config.auth_token)
		self.service = self.connectGmail()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		logger.debug('Notification done')

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

	def createEmailMessage(self, sender, to, subject, message_text):
		message = MIMEText(message_text)
		message['to'] = to
		message['from'] = sender
		message['subject'] = subject
		return {'raw': base64.urlsafe_b64encode(message.as_string())}

	def sendEmail(self, service, user_id, message):
		try:
			message = (service.users().messages().send(userId=user_id, body=message)
					   .execute())
			print('Message Id: %s' % message['id'])
			return message
		except errors.HttpError as error:
			print('An error occurred: %s' % error)

	def sendSMS(self, dict):
		logger.debug('Sending sms')
		timestamp = dict['timestamp'].astimezone(timezone('Australia/Sydney')).strftime('%Y-%m-%d %H:%M:%S')
		message = self.smsclient.messages.create(
			body=self.smsMessage.format(
				timestamp, dict['title'], dict['price'], dict['link']),
			from_='+14843010951',
			to='+61478790532'
		)
		logger.debug('sms sent')
