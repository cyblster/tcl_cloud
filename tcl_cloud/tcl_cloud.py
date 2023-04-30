import requests
import hashlib
import time
from requests_aws4auth import AWS4Auth


class TclCloud:
    def __init__(self, username: str, password: str, region: str):
        self.__session = requests.session()
        self.__user_agent = 'aws-sdk-iOS/2.26.2 iOS/16.4.1 ru_RU'

        self._username = username
        self._password = password
        self._region = region
        self._tcl_id = None
        self._access_token = None
        self._cognito_id = None
        self._cognito_token = None
        self._cloud_url = None
        self._cloud_region = None
        self._mqtt_endpoint = None
        self._access_key_id = None
        self._secret_key = None
        self._session_token = None
        self._signature = None

        self._login_step_1()
        self._login_step_2()
        self._login_step_3()
        self._login_step_4()

    def _login_step_1(self):
        url = 'https://rus.account.tcl.com/account/login'
        headers = {
            'User-Agent': self.__user_agent
        }
        params = {
            'clientId': 19426210
        }
        data = {
            'captchaRule': 3,
            'channel': 'web',
            'countryAbbr': self._region,
            'password': hashlib.md5(self._password.encode('utf-8')).hexdigest(),
            'username': self._username
        }
        response_json = self.__session.post(url, params=params, json=data, headers=headers).json()

        if 'user' not in response_json:
            raise ValueError('Invalid username or password')

        self._tcl_id = response_json['user']['username']
        self._access_token = response_json['token']

    def _login_step_2(self):
        url = 'https://prod-center.aws.tcljd.com/v2/global/cloud_url_get'
        headers = {
            'User-Agent': self.__user_agent
        }
        data = {
            'ssoId': self._tcl_id,
            'ssoToken': self._access_token
        }
        response_json = self.__session.post(url, json=data, headers=headers).json()

        self._cloud_url = response_json['data']['cloud_url']
        self._cloud_region = response_json['data']['cloud_region']

    def _login_step_3(self):
        url = f'{self._cloud_url}/v3/auth/refresh_tokens'
        headers = {
            'User-Agent': self.__user_agent
        }
        data = {
            'appId': 'f6hek6hdpt64jrw596',
            'ssoToken': self._access_token,
            'lang': self._region.lower(),
            'userId': self._tcl_id
        }
        response_json = self.__session.post(url, json=data, headers=headers).json()

        self._cognito_id = response_json['data']['cognitoId']
        self._cognito_token = response_json['data']['cognitoToken']
        self._mqtt_endpoint = response_json['data']['mqttEndpoint'].replace('wss://', '').split(':')[0]

        return True

    def _login_step_4(self):
        url = f'https://cognito-identity.{self._cloud_region}.amazonaws.com'
        headers = {
            'User-Agent': self.__user_agent,
            'Content-Type': 'application/x-amz-json-1.1',
            'X-Amz-Target': 'AWSCognitoIdentityService.GetCredentialsForIdentity',
            'X-Amz-Date': time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        }
        data = {
            'Logins': {
                'cognito-identity.amazonaws.com': self._cognito_token
            },
            'IdentityId': self._cognito_id
        }
        response_json = self.__session.post(url, json=data, headers=headers).json()

        self._access_key_id = response_json['Credentials']['AccessKeyId']
        self._secret_key = response_json['Credentials']['SecretKey']
        self._session_token = response_json['Credentials']['SessionToken']

    def get_info(self, device_id: str):
        url = f'https://{self._mqtt_endpoint}/things/{device_id}/shadow'
        headers = {
            'User-Agent': self.__user_agent,
            'Content-Type': 'application/x-amz-json-1.0'
        }
        response = self.__session.get(url, headers=headers, auth=AWS4Auth(
            self._access_key_id,
            self._secret_key,
            self._cloud_region,
            'iotdata',
            session_token=self._session_token
        ))

        response_json = response.json()
        if response.status_code == 403:
            if response_json['message'] is None:
                raise ValueError('Invalid device id')

            self._login_step_3()
            self._login_step_4()
            return self.get_info(device_id)

        return response_json

    def send_action(self, device_id: str, **data):
        url = f'https://{self._mqtt_endpoint}/topics/$aws/things/{device_id}/shadow/update'
        headers = {
            'User-Agent': self.__user_agent,
            'Content-Type': 'application/x-amz-json-1.0'
        }
        params = {
            'qos': 0
        }
        data = {
            'state': {
                'desired': data
            },
            'clientToken': 'mqtt_ios'
        }
        response = self.__session.post(url, params=params, json=data, headers=headers, auth=AWS4Auth(
            self._access_key_id,
            self._secret_key,
            self._cloud_region,
            'iotdata',
            session_token=self._session_token
        ))

        response_json = response.json()
        if response.status_code == 403:
            if response_json['message'] is None:
                raise ValueError('Invalid device id')

            self._login_step_3()
            self._login_step_4()
            return self.send_action(device_id, **data)

        return True
