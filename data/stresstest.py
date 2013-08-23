# Stress-tests; requires splinter

import cookielib
import sys, re, os
from splinter import Browser
import time
import operator
import random
import threading

NUM_SUBMITS = 100
CHAT_URL = 'http://vitalmeeting.com/meeting/qrbmbmltkjkhunh'
SIGNUP_URL = 'http://vitalmeeting.com/signup/'
SLEEP_SECS = 0.25
NUM_THREADS = 4

class ThreadClass(threading.Thread):
	def run(self):
		username = ''
		password = 'password'

		random.seed()

		for i in range(10):
			username += chr(int(random.random()*25)+97)

		username += '@vitalmeeting.com'

		index = ''
		for i in range(4):
			index += chr(int(random.random()*9)+48)

		with Browser() as browser:
			browser.visit(SIGNUP_URL)
			browser.fill('first_name', 'Test')
			browser.fill('last_name', index)
			browser.fill('email', username)
			browser.fill('password', password)
			browser.fill('retype', password)
			browser.find_by_tag('button')[1].click()

			browser.visit(CHAT_URL)
			browser.find_by_name('join_meeting').first.click()

			for i in range(NUM_SUBMITS):
				time.sleep(SLEEP_SECS)
				browser.fill('usermsg', 'stress test')
				browser.find_by_name('submitmsg').first.click()

def test_chat():
	for i in range(NUM_THREADS):
		t = ThreadClass()
		t.start()

test_chat()
