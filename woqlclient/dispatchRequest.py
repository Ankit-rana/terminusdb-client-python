
#from .errorMessage import ErrorMessage
from .const import Const as const
import requests

from .utils import Utils

from base64 import b64encode


class DispatchRequest:

    def __init__(self):
        pass

    @staticmethod
    def __getCall(url, headers, payload):
        url = Utils.addParamsToUrl(url, payload)

        return requests.get(url, headers=headers)

    @staticmethod
    def __postCall(url, headers, payload):
        headers['content-type'] = 'application/json'
        return requests.post(url, json=payload, headers=headers)

    @staticmethod
    def __deleteCall(url, headers, payload):
        url = Utils.addParamsToUrl(url, payload)
        return requests.delete(url, headers=headers)

    @staticmethod
    def __autorizationHeader(key):
        headers = {}

        # if (payload and ('terminus:user_key' in  payload)):
        # Utils.encodeURIComponent(payload['terminus:user_key'])}
        headers = {'Authorization': 'Basic %s' % b64encode(
            (':' + key).encode('utf-8')).decode('utf-8')}
        # payload.pop('terminus:user_key')
        return headers

    @classmethod
    def sendRequestByAction(cls, url, action, key, payload={}):
        print("Sending to URL__", url)
        print("sendRequestByAction_____", action)
        try:
            requestResponse = None
            headers = cls.__autorizationHeader(key)

            if action in [const.CONNECT, const.GET_SCHEMA, const.CLASS_FRAME, const.WOQL_SELECT, const.GET_DOCUMENT]:
                requestResponse = cls.__getCall(url, headers, payload)

            elif action in [const.DELETE_DATABASE, const.DELETE_DOCUMENT]:
                requestResponse = cls.__deleteCall(url, headers, payload)

            elif action in [const.CREATE_DATABASE, const.UPDATE_SCHEMA, const.CREATE_DOCUMENT, const.WOQL_UPDATE]:
                requestResponse = cls.__postCall(url, headers, payload)

            if(requestResponse.status_code == 200):
                return requestResponse.json()  # if not a json not it raises an error
            else:
                requestResponse.raise_for_status()

        # to be review
        # the server in the response return always contet-type application/json
        except ValueError as err:
            # if the response type is not a json
            print("Value Error", err)
            return requestResponse.text
        """
        except requests.exceptions.RequestException as err:
            print ("Request Error",err)
        except requests.exceptions.HTTPError as err:
            print ("Http Error:",err)
        except requests.exceptions.ConnectionError as err:
            print ("Error Connecting:",err)
        except requests.exceptions.Timeout as err:
            print ("Timeout Error:",err)
        """
