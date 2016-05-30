# -*- coding: utf-8 -*-
#
# Get Edenred lunch card balance.
#
# Author: Jarno Tuovinen
# License: MIT
#

import os, sys, requests, json, logging, time
from optparse import OptionParser
from urlparse import urljoin
from datetime import datetime
from base64 import standard_b64encode

USERNAME="username" # f.e. jarnotuo
PASSWORD="password"

#import socks
#import socket
#socks.setdefaultproxy(socks.PROXY_TYPE_HTTP, "192.168.1.174", 8787)
#socket.socket = socks.socksocket

url = "https://ticket.edenred.fi"
#url = "http://localhost:12000"

FORMAT = '%(message)s'
__version__ = '0.0.1'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('edenblue')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

verify = False

class EdenBlue:
  global verify
  url = None
  token = None

  """ Simple constructor, defaults against cloud.testdroid.com
  """
  def __init__(self, username, password, url = "https://ticket.edenred.fi"):
    self.url = url
    self.username = username
    self.password = password

  def get_encoded(self):
    unencoded = self.username + ':' +self.password
    encoded = standard_b64encode(unencoded)
    return encoded

  def get_token(self):
    if self.token is None:
      res = self.post("UserLogin2", {"credentials": self.get_encoded()})
      if res.status_code != 200:
        logger.error('Unexpected response status {}'.format(res.status_code))
        sys.exit(1)
      reply = res.json()
      logger.debug('Response JSON:\n{}\n'.format(reply))
      self.token = reply['UserLogin2Result']['UserSessionToken']
      if self.token is None:
        logger.error("Authentication error - {}".format(reply['UserLogin2Result']['Response']))
        sys.exit(1)
      logger.debug('New token: {}'.format(self.token))
    else:
      logger.debug('Using existing token: {}'.format(self.token))
    return self.token

  """ Helper method for getting necessary headers to use for API calls, including authentication
  """
  def _build_headers(self):
    return {"Content-Type": "application/json",
            "Accept":       "application/json",
            "User-Agent":   "Apache-HttpClient/UNAVAILABLE (java 1.4)"}

  """ POST against API resources
  """
  def post(self, path=None, payload=None, headers={}):
    payload = json.dumps(payload)
    logger.debug("\nPOST\n  path={}\n  payload={}\n".format(path, payload))
    headers = dict(self._build_headers().items() + headers.items())
    url = "%s/WebServices/UserAccount.svc/%s" % (self.url, path)
    return requests.post(url, data=payload, headers=headers, verify=verify)

  def get_balance(self):
    logger.debug('Get balance')
    res = self.post('GetAccountBalance', {"serviceTypeCode":"TR","userSessionToken":self.get_token()})
    if res.status_code != 200:
      logger.error('Unexpected response status {}'.format(res.status_code))
      sys.exit(1)
    reply = res.json()
    logger.debug('Response JSON:\n{}\n'.format(reply))
    balance = reply['GetAccountBalanceResult']['BalanceField']['AmountField']
    currency = reply['GetAccountBalanceResult']['BalanceField']['CurrencyCodeField']
    logger.debug('Original balance {}'.format(balance))
    balance = float(balance) / 100.0
    logger.debug('Real balance {} {}'.format(balance, currency))
    return (balance, currency)

  def print_balance(self):
    balance = self.get_balance()
    logger.info('Your balance: {} {}'.format(balance[0], balance[1]))

  def logout(self):
    logger.debug('Logout')
    res = self.post('UserLogout', {"userSessionToken":self.get_token()})
    if res.status_code != 200:
      logger.error('Unexpected response status {}'.format(res.status_code))
      sys.exit(1)
    reply = res.json()
    logger.debug('Response JSON:\n{}\n'.format(reply))
    result = reply['UserLogoutResult']
    if result == 'OK;Logged out':
      logger.debug('Logout successful')
      sys.exit(0)
    else:
      logger.debug('Logout failed - {}'.format(result))
      sys.exit(1)

def main():
  global url
  edenblue = EdenBlue(USERNAME, PASSWORD)
  token = edenblue.get_token()
  logger.debug("Token: {}".format(token))
  edenblue.print_balance()
  edenblue.logout()

if __name__ == '__main__':
  main()

