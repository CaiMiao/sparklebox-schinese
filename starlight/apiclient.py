#!/usr/bin/python
# -!- coding: utf-8 -!-
#
# Copyright 2016 Hector Martin <marcan@marcan.st>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64, msgpack, hashlib, random, time, os
from tornado import httpclient
import binascii, pyaes
import json
import traceback

# laziness
def VIEWER_ID_KEY():
    return os.getenv("VC_AES_KEY", "").encode("ascii")

def SID_KEY():
    return os.getenv("VC_SID_SALT", "").encode("ascii")

def decrypt_cbc(s, iv, key):
    e = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
    clear = e.feed(s)
    clear += e.feed()
    return clear

def encrypt_cbc(s, iv, key):
    e = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
    clear = e.feed(s)
    clear += e.feed()
    return clear

def is_usable():
    return all([x in os.environ for x in ["VC_ACCOUNT", "VC_AES_KEY", "VC_SID_SALT"]]) \
        and not os.getenv("DISABLE_AUTO_UPDATES", None)

class ApiClient(object):
    BASE = "https://apis.game.starlight-stage.jp"
    SHARED_INSTANCE = None

    @classmethod
    def shared(cls):
        if cls.SHARED_INSTANCE is None:
            print("ApiClient.shared is creating the shared instance")
            user_id, viewer_id, udid = os.getenv("VC_ACCOUNT", "::").split(":")
            the_client = cls(user_id, viewer_id, udid)
            cls.SHARED_INSTANCE = the_client
        return cls.SHARED_INSTANCE

    def __init__(self, user, viewer_id, udid, res_ver="10013600"):
        self.user = user
        self.viewer_id = viewer_id
        self.udid = udid
        self.sid = None
        self.res_ver = res_ver

    def lolfuscate(self, s):
        return "%04x" % len(s) + "".join(
            "%02d" % random.randrange(100) +
            chr(ord(c) + 10) + "%d" % random.randrange(10)
            for c in s) + "%032d" % random.randrange(10**32)

    def unlolfuscate(self, s):
        return "".join(chr(ord(c) - 10) for c in s[6::4][:int(s[:4], 16)])

    async def call(self, path, args):
        vid_iv = b"1111111111111111"
        args["viewer_id"] = vid_iv + base64.b64encode(
            encrypt_cbc(bytes(self.viewer_id, "ascii"),
                        vid_iv,
                        VIEWER_ID_KEY()))
        plain = base64.b64encode(msgpack.packb(args))
        # I don't even
        key = base64.b64encode(bytes(random.randrange(255) for i in range(32)))[:32]
        msg_iv = binascii.unhexlify(self.udid.replace("-","").encode("ascii"))
        body = base64.b64encode(encrypt_cbc(plain, msg_iv, key) + key)
        sid = self.sid if self.sid else str(self.viewer_id) + self.udid
        headers = {
            "PARAM": hashlib.sha1(bytes(self.udid + str(self.viewer_id) + path, "ascii") + plain).hexdigest(),
            "KEYCHAIN": "",
            "USER-ID": self.lolfuscate(str(self.user)),
            "CARRIER": "google",
            "UDID": self.lolfuscate(self.udid),
            "APP-VER": os.environ.get("VC_APP_VER", "1.9.1"), # in case of sent
            "RES-VER": str(self.res_ver),
            "IP-ADDRESS": "127.0.0.1",
            "DEVICE-NAME": "Nexus 42",
            "X-Unity-Version": os.environ.get("VC_UNITY_VER", "5.4.5p1"),
            "SID": hashlib.md5(bytes(sid, "ascii") + SID_KEY()).hexdigest(),
            "GRAPHICS-DEVICE-NAME": "3dfx Voodoo2 (TM)",
            "DEVICE-ID": hashlib.md5(b"Totally a real Android").hexdigest(),
            "PLATFORM-OS-VERSION": "Android OS 13.3.7 / API-42 (XYZZ1Y/74726f6c6c)",
            "DEVICE": "2",
            "Content-Type": "application/x-www-form-urlencoded", # lies
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13.3.7; Nexus 42 Build/XYZZ1Y)",
        }

        req = httpclient.HTTPRequest(self.BASE + path, method="POST", headers=headers, body=body)
        try:
            response = await httpclient.AsyncHTTPClient().fetch(req)
        except httpclient.HTTPError as e:
            print("Got HTTP error while talking to API:", e.code)
            return (response, None)
        except Exception as e:
            print("Unexpected error: ", e)
            traceback.print_exc()
            return (response, None)

        reply = base64.b64decode(response.buffer.read())
        plain = decrypt_cbc(reply[:-32], msg_iv, reply[-32:]).split(b"\0")[0]
        msg = msgpack.unpackb(base64.b64decode(plain))
        try:
            self.sid = msg["data_headers"]["sid"]
        except KeyError:
            pass

        return (response, msg)

async def versioncheck_bare():
    client = ApiClient.shared()
    args = {
        "campaign_data": "",
        "campaign_user": 1337,
        "campaign_sign": hashlib.md5(b"All your APIs are belong to us").hexdigest(),
        "app_type": 0,
    }
    return await client.call("/load/check", args)

async def versioncheck():
    versioncheck_host = os.environ.get("VERSIONCHECK_PROXY")
    if versioncheck_host:
        path = "/api/v1/versioncheck"
        req = httpclient.HTTPRequest(versioncheck_host + path, method="GET")
        try:
            resp = await httpclient.AsyncHTTPClient().fetch(req)
            reply = json.loads(resp.body.decode("utf8"))
            if "version" in reply:
                return (resp, {b"data_headers": {
                    b"required_res_ver": str(reply["version"]).encode("ascii")
                }})
            else:
                return await versioncheck_bare()
        except httpclient.HTTPError as e:
            print("Got HTTP error while talking to versioncheck proxy:", e.code)
            return await versioncheck_bare()
        except Exception as e:
            print("Unexpected error: ", e)
            traceback.print_exc()
            return await versioncheck_bare()
    else:
        return await versioncheck_bare()

async def gacha_rates(gacha_id):
    client = ApiClient.shared()
    args = {
        "gacha_id": gacha_id,
        "timezone": "-07:00:00",
    }
    return await client.call("/gacha/get_rate", args)
