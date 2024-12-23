#!/usr/bin/python3                                                                                                                         
#VERSION 2.0
import json
import sys
import requests
import pprint
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from time import gmtime,strftime
from datetime import datetime,timedelta,date
import time
import os
import re
import base64
import urllib
import xml.etree.ElementTree
import xml.etree.ElementTree as ET
import ipaddress
from requests.auth import HTTPBasicAuth
import ssl
import email, hmac, hashlib
import six
import codecs


class CatsException(Exception):
    pass

#
# CATS
# base class, from which to inherit, dealing mainly with errors, exceptions and logging
#  implements basic get, put, post, delete methods returning result to JSON
#
class CATS:

    def __init__(self,debug,logfile):
        self.debug = debug
        self.logfile = logfile
        self.authwithclientcert = False
        self.clientcert = ""
        self.clientkey = ""
        self.clientkeypassword = ""
        self.servercert = ""
        
    def log_debug(self,message):
        if self.debug:
            if self.logfile:
                logfile = open(self.logfile,"a")
                logfile.write("CATS @ " + str(datetime.now()) + " @ " + message+"\n")
                logfile.close()
            else:
                print("CATS @ " + str(datetime.now()) + " @ " + message)                

    def exception_string(self,err):
    
        (exc_type, exc_obj, exc_tb) = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errorstring = "Exception! {} {} {} {} {}\n ".format(str(err),exc_type,fname,exc_tb.tb_lineno,exc_obj)
        self.log_debug(errorstring)
        return errorstring

    def get_ssl_context(self):
        self.log_debug("Creating SSL context {} {} {} {}".format(self.clientcert,self.clientkey,self.clientkeypassword,self.servercert))
        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        if self.clientcert is not None:
            context.load_cert_chain(certfile=self.clientcert,
                                    keyfile=self.clientkey,
                                    password=self.clientkeypassword)
        context.load_verify_locations(capath=self.servercert)
        self.log_debug("Created SSL context")        
        return context
    
    def get(self,url,headers,verify):
        try:
            self.log_debug("GET  " + url)
            self.log_debug("HEADERS " +str(headers))
            r = requests.get(url,verify=False,headers=headers)
            status_code = r.status_code
            if  (status_code / 100) == 2:
                if "Set-Cookie" in r.headers:
                    if r.headers["Set-Cookie"][:]:
                        self.cookie = r.headers["Set-Cookie"][:]                        
                        self.log_debug("COOKIE SET:"+self.cookie)                            
                self.log_debug("status is " +  str(status_code))
                self.log_debug("text is " + r.text)
                json_response = json.loads(r.text)
                json_response = r.json()
                #result = { "catsresult": "OK", "info": "GET successful"  }
                #json_response.update(result)
                return json_response
            else:
                errorstring = "Error in get url:{} statuscode:{} text {}".format(url,str(status_code),r.text)                                
                self.log_debug(errorstring)                
                raise ValueError(errorstring)                                
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                                        


    def delete(self,headers,url,verify):

        try:
            self.log_debug("DELETE"  + url)
            self.log_debug(str(headers))
            r = requests.delete(url=url,headers=headers,verify=verify)
            status_code = r.status_code
            if  (status_code // 100 ==2):
                result = { "catsresult": "OK", "info": "Delete successful" }
                return result
            else:
                errorstring = "Error in get {} {} {}".format(url,str(status_code),r.text)                
                self.log_debug(errorstring)                
                raise ValueError(errorstring)                                

        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                                                    

    def post(self,url,headers,data,verify):

        try:
            self.log_debug("POST:   " + url)
            self.log_debug("HEADERS:" + str(headers))
            self.log_debug("DATA:   " + str(data))

            if not self.authwithclientcert:
                r = requests.post(url,data=data,headers=headers,verify=verify)
                if r.status_code // 100 == 2:
                    self.log_debug(str(r.status_code))                    
                    if "Set-Cookie" in r.headers:
                        if r.headers["Set-Cookie"][:]:
                            self.cookie = r.headers["Set-Cookie"][:]
                            self.log_debug("COOKIE SET:"+self.cookie)
                    self.log_debug(r.text)
                    if r.status_code == 204:
                        ### empty response, e.g. the requested item does not exist
                        ### avoid exception in json.loads
                        rsp = {}
                    else:
                        rsp = json.loads(r.text)
                    return rsp
                else:
                    errorstring = "Error in post {} {} {}".format(url,str(r.status_code),r.text)
                    self.log_debug(errorstring)                
                    raise ValueError(errorstring)                                
            else:

                json_string = data
                self.log_debug('  url=' + url)            
                self.log_debug('  request=' + json_string)
                ssl_context = self.get_ssl_context()
                handler = urllib.request.HTTPSHandler(context=ssl_context)
                opener = urllib.request.build_opener(handler)
                rest_request = urllib.request.Request(url=url, headers=headers,data=str.encode(json_string))
                self.log_debug("Opening HTTPS request with SSL context")
                rest_response = opener.open(rest_request)
                self.log_debug("Successfully opened HTTP Request")
                self.log_debug("rest response {}".format(str(rest_response)))
                response = rest_response.read().decode()
                self.log_debug('  response=' + response)
                rsp = json.loads(response)
                rsp.update({"catsresult": "OK"})
                return rsp
            
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err


    def put(self,headers,url,data,verify=False):

        try:
            self.log_debug("PUT:" +url)
            self.log_debug("PUT:" +data)            
            r = requests.put(url=url,headers=headers,data=data,verify=verify)
            status_code = r.status_code
            if  (status_code // 100) == 2:
                result = {"catsresult":"OK"}
                return result
            else:
                errorstring = "Error in get {} {} {}".format(url,str(status_code),r.text)
                self.log_debug(errorstring)                
                raise ValueError(errorstring)                                
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err            


#
#   Class implementing parts of Cisco DNA Center API
#
#
class DNAC(CATS):
    
    def __init__(self,controller_ip, username, password,debug,logfile):
        CATS.__init__(self,debug,logfile)
        self.controller_ip = controller_ip
        login_url = "https://{0}/dna/system/api/v1/auth/token".format(controller_ip)

        
        result = requests.post(url=login_url, auth=HTTPBasicAuth(username,password), verify=False)
## todo inconsistent error handling
        result.raise_for_status()        
        token = result.json()["Token"]
        self.auth_token =  {
            "controller_ip": controller_ip,
            "token": token
        }

    def get_auth_token(self):
        return self.auth_token

    def dnac_get(self,path):
        url = "https://{}/api/v1/{}".format(self.controller_ip,path)
        headers = {'X-auth-token' : self.auth_token["token"]}
        return(self.get(url,headers,verify=False))

    def get_from_ip(self,ip):
        return(self.dnac_get("network-device/ip-address/{}".format(ip)))

    def get_modules(self,this_id):
        return self.dnac_get("network-device/module?deviceId={}".format(this_id))
    
#   Class implementing parts of FTD API
#
#
class FTD(CATS):
    
    def __init__(self,host,username,password,debug,logfile):
        
        CATS.__init__(self,debug,logfile)
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization':'Bearer'
        }
        path = "/api/fdm/v1/fdm/token"
        self.server = "https://"+host
        url = self.server + path
        body = {
            "grant_type" : "password",
            "username"   : username,
            "password"   : password,
            }
        self.access_token = ""
        self.refresh_token = ""

        try:
            rsp = self.post(url, headers=self.headers,data=json.dumps(body), verify=False)
            self.access_token = rsp["access_token"]
            self.headers["Authorization"] = "Bearer {}".format(self.access_token)
            self.refresh_token = rsp["refresh_token"]
            
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err            

    def ftdget(self,api):
        api_path= "/api/fdm/v1" + api
        url = self.server+api_path
        return (self.get(url=url,headers=self.headers,verify=False))
        
    def ftdpost(self,api,post_data):
        api_path= "/api/fdm/v1/" + api
        url = self.server+api_path
        return (self.post(url=url,data=json.dumps(post_data),headers=self.headers,verify=False))

    def ftdput(self,api,data):
        api_path= "/api/fdm/v1/" + api
        url = self.server+api_path
        return (self.put(url=url,data=json.dumps(data),headers=self.headers,verify=False))
    
    def ftddelete(self,api):
        api_path= "/api/fdm/v1/" + api
        url = self.server+api_path
        return (self.delete(url=url,headers=self.headers,verify=False))
    
    def get_access_token(self):
        return self.access_token

    def find_item(self,rsp,nametosearch,thisname):
        self.log_debug(" {}  {} ".format(nametosearch,thisname))
        for item in rsp["items"]:
            if item[nametosearch] == thisname:
                return(item)

        return(None)
        
    def interfaces_get(self,name=""):
        return (self.ftdget("/devices/default/interfaces?limit=10000"))

    def interface_change_by_name(self,hardwarename,ifname,ipv4address,ipv4mask):
        putdata = {
            "description": "kalle",
            "duplexType": "AUTO",
            "enabled": True,
            "gigabitInterface": True,
            "hardwareName": "GigabitEthernet0/0",
#            "id": "8d6c41df-3e5f-465b-8e5a-d336b282f93f",
            "ipv4": {
                "addressNull": False,
                "defaultRouteUsingDHCP": False,
                "dhcp": False,
                "ipAddress": {
                    "ipAddress": ipv4address,
                    "netmask": ipv4mask,
                    "type": "ipv4address"
                },
                "ipType": "STATIC",
                "type": "interfaceipv4"
            },
            "ipv6": {
                "autoConfig": True,
                "dadAttempts": 1,
                "dhcpForManagedConfig": False,
                "dhcpForOtherConfig": False,
                "enableRA": False,
                "enabled": True,
                "ipAddresses": [],
#                "linkLocalAddress": {
#                    "ipAddress": null,
#                    "type": "ipv6address"
#                },
                "prefixes": [],
                "type": "interfaceipv6"
            },
            "linkState": "UP",
#            "links": {
#                "self": "https://198.18.133.8/api/fdm/v1/devices/default/interfaces/8d6c41df-3e5f-465b-8e5a-d336b282f93f"
#            },
            "managementInterface": False,
            "managementOnly": False,
            "mtu": 1500,
            "name": "outside",
            "speedType": "AUTO",
            "subInterfaces": [],
            "tenGigabitInterface": False,
            "type": "physicalinterface",
            "version": ""
        }

        rsp = self.interfaces_get()
        self.log_debug(json.dumps(rsp,indent=4,sort_keys=True))
        found_item = self.find_item(rsp=rsp,nametosearch="hardwareName",thisname=hardwarename)
        if found_item:
            putdata["id"] = found_item["id"]
            putdata["version"] = found_item["version"]
            return(self.ftdput(api="devices/default/interfaces/{}".format(found_item["id"]),data=putdata))
        else:
            errorstring = "Could not perform operation"
            self.log_debug(errorstring)                
            raise ValueError(errorstring)                                

        
        
    def network_object_create(self,name,value):

        if '/' in value:
            self.log_debug("found /")
            subType = "NETWORK"
        else:
            self.log_debug("not found /")
            subType = "HOST"
            
        postdata = {
            "name" : name,
            "description" : "testdesc",
            "subType"     :subType,
            "value"     :value,
            "type" : "networkobject"
        }
        return(self.ftdpost("object/networks",postdata))

    def network_objects_get(self,name=""):
        return (self.ftdget("/object/networks?limit=10000"))

    def network_object_delete_by_name(self,name):
        rsp = self.network_objects_get()
        found_item = self.find_item(rsp,"name",name)
        if found_item:
            return(self.ftddelete(api="object/networks/{}".format(found_item["id"])))
        else:
            errorstring = "Could not perform operation"
            self.log_debug(errorstring)                
            raise ValueError(errorstring)                                
    
    def network_object_change_by_name(self,name,value):

        putdata = {
            "name": name,
            "description": "string",
            "subType": "HOST",
            "value": value,
            "type": "networkobject",
            "version": "",
        }
        
        rsp = self.network_objects_get()
        found_id = None
        for item in rsp["items"]:
            if item["name"] == name:
                found_id = item["id"]
                found_version = item["version"]
                break
        if found_id:
            putdata["id"] = found_id
            putdata["version"] = found_version
            return(self.ftdput(api="object/networks/{}".format(found_id),data=putdata))
        else:
            errorstring = "Could not perform operation"
            self.log_debug(errorstring)                
            raise ValueError(errorstring)
        
#    
#   Class implementing parts of FMC API
#
#
class FMC(CATS):
    
    def __init__(self,host,username,password,debug,logfile):
        
        CATS.__init__(self,debug,logfile)
        self.headers = {'Content-Type': 'application/json'}
        path = "/api/fmc_platform/v1/auth/generatetoken"
        self.server = "https://"+host
        url = self.server + path
        try:
            if debug:
                print("POST url {} username {} password {}".format(url,username,password))
            r = requests.post(url, headers=self.headers, auth=requests.auth.HTTPBasicAuth(username,password), verify=False)
            auth_headers = r.headers
            token = auth_headers.get('X-auth-access-token', default=None)
            self.uuid = auth_headers.get('DOMAIN_UUID', default=None)
            self.headers['X-auth-access-token'] = token
            if token == None:
                self.log_debug("No Token found, I'll be back terminating....")
                raise ValueError("No token in response!")
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                        

        
    def fmcget(self,api):
        api_path= "/api/fmc_config/v1/domain/" + self.uuid + api
        url = self.server+api_path
        return (self.get(url=url,headers=self.headers,verify=False))

    def fmcpost(self,api,post_data):
        api_path= "/api/fmc_config/v1/domain/" + self.uuid + api
        url = self.server+api_path
        return (self.post(url=url,data=post_data,headers=self.headers,verify=False))

    def fmcput(self,api,put_data):
        api_path= "/api/fmc_config/v1/domain/" + self.uuid + api
        url = self.server+api_path
        return (self.put(url=url,data=put_data,headers=self.headers,verify=False))

    def getFileTypes(self):
        return self.fmcget(api="/object/filetypes?offset=0&limit=300")
    
    def createAccessPolicy(self,name,defaultAction="BLOCK"):
        postdata = json.dumps({"name":name,
                    "name":name,
                    "type":"AccessPolicy",
                    "defaultAction": {
                        "action": defaultAction
                    }})
        rsp = self.fmcpost(api="/policy/accesspolicies",post_data=postdata)
        return(rsp)

    def getZoneUUID(self,zoneName):
        rsp = self.fmcget(api="/object/securityzones")
        items = rsp["items"]
        zoneUUID = 0
        for i in items:
            if i["name"] == zoneName:
                zoneUUID = i["id"]
                break
        return zoneUUID
    
    def getAccessPolicyUUID(self,policyName):
        rsp = self.fmcget(api="/policy/accesspolicies")
        items = rsp["items"]
        policyUUID = 0
        for i in items:
            if i["name"] == policyName:
                policyUUID = i["id"]
                break
        return policyUUID

    def createAccessPolicyRule(self,policyName,ruleName,sourceZone,destinationZone):

        policyUUID = self.getAccessPolicyUUID(policyName)
        szUUID = self.getZoneUUID(sourceZone)
        dzUUID = self.getZoneUUID(destinationZone)
        postdata = json.dumps({
            "action": "ALLOW",
            "enabled": True,
            "type": "AccessRule",
            "name": ruleName,
            "sendEventsToFMC": True,
            "logBegin": True,
            "logEnd": True,
  
            "sourceZones": {
                "objects": [
                {
                    "name": sourceZone,
                    "id": szUUID,
                    "type": "SecurityZone"
                }
                ]
            },
            "destinationZones": {
                "objects": [
                {
                "name": destinationZone,
                "id": dzUUID,
                "type": "SecurityZone"
                }
                ]
            },
  
        })
        rsp = self.fmcpost(api="/policy/accesspolicies/{}/accessrules".format(policyUUID),post_data=postdata)

    def getAccessPolicies(self):
        return self.fmcget(api="/policy/accesspolicies")

    def getAccessPolicyRules(self,accesspolicy_id):
        return self.fmcget(api="/policy/accesspolicies/{}/accessrules".format(accesspolicy_id))

    def getAccessPolicyRule(self,accesspolicy_id,rule_id):
        return self.fmcget(api="/policy/accesspolicies/{}/accessrules/{}".format(accesspolicy_id,rule_id))

    def getAccessPolicyRulesByPolicyName(self,policy_name):
        final_result = {"items": []}
        rsp = self.getAccessPolicies()
        items = rsp["items"]
        policy_id = ""

        for item in items:
                if item["name"] == policy_name:
                        policy_id = item["id"]
        if policy_id:
            rsp = self.getAccessPolicyRules(policy_id)
            items = rsp["items"]
            for item in items:
                rule_id = item["id"]
                rsp = self.getAccessPolicyRule(policy_id,rule_id)
                final_result["items"].append(rsp)
            return(final_result)
        else:
            errorstring = "Could not perform operation - could not finde policy {}".format(policy_name)
            self.log_debug(errorstring)                
            raise ValueError(errorstring)

    def getNetworkObjects(self):
        return self.fmcget(api="/object/networks")
    
    def getNetworkObjectByName(self,name):
        rsp = self.fmcget(api="/object/networks")
        items = rsp["items"]
        for item in items:
            if item["name"] == name:
                return item
        return None

    def createNetworkObject(self,name,value="",overridable=False,description="",objecttype="Network"):
        postdata = json.dumps({"name":name,
                    "value":value,
                    "overridable": overridable,
                    "description": description,
                    "type":objecttype})
        rsp = self.fmcpost(api="/object/networks",post_data=postdata)

    def createHostObject(self,name,value="",overridable=False,description="",objecttype="Host"):
        postdata = json.dumps({"name":name,
                    "value":value,
                    "overridable": overridable,
                    "description": description,
                    "type":objecttype})
        rsp = self.fmcpost(api="/object/hosts",post_data=postdata)
    
    def createSecurityZone(self,name,interfacemode):
        postdata = json.dumps({
            "type": "SecurityZone",
            "name": name,
            "interfaceMode": interfacemode,
            "interfaces": []})
        rsp = self.fmcpost(api="/object/securityzones",post_data=postdata)
    
    def createDeviceGroup(self,name):
        postdata = json.dumps({"name":name,
                    "name":name,
                    "type":"DeviceGroup"})
        rsp = self.fmcpost(api="/devicegroups/devicegrouprecords",post_data=postdata)
        return(rsp)
    def getPlatformPolicies(self):
        rsp = self.fmcget(api="/policy/ftdplatformsettingspolicies")
        return(rsp)
    def getPlatformHTTPsettings(self,platformPolicy):
        rsp = self.getPlatformPolicies()
        items = rsp["items"]
        platformUUID = 0
        for i in items:
            if i["name"] == platformPolicy:
                platformUUID = i["id"]
                break
        rsp = self.fmcget(api="/policy/ftdplatformsettingspolicies/{}/httpaccesssettings/{}".format(platformUUID,platformUUID))
        return(rsp)
    def createPlatformPolicy(self,name):
        postdata = json.dumps({"name":name,
                    "name":name,
                    "type":"FTDPlatformSettingsPolicy"})
        rsp = self.fmcpost(api="/policy/ftdplatformsettingspolicies",post_data=postdata)
    
    def createPlatformHTTPsetting(self,platformPolicy,zone,networkobject,port=9443):
        rsp = self.getPlatformPolicies()
        items = rsp["items"]
        platformUUID = 0
        for i in items:
            if i["name"] == platformPolicy:
                platformUUID = i["id"]
                break
        zID = self.getZoneUUID(zoneName=zone)
        postdata = json.dumps({
        "id": platformUUID,
        "enableHttpServer": True,
        "port": port,
        "httpConfiguration": [
        {
            "ipAddress": {
                # "id": xxx,
                "name": networkobject,
                "type": "Network"
            },
            "interfaces": {
                "objects": [
                {
                    "name": zone,
                    "id": zID,
                    "type": "SecurityZone"
                },
            ],
            }
        },
        ]
        })
        rsp = self.fmcput(api="/policy/ftdplatformsettingspolicies/{}/httpaccesssettings/{}".format(platformUUID,platformUUID),put_data=postdata)
        return(rsp)
    
    def configure_interface(self,devicename,ifname,name,ipv4address,ipv4mask):
        rsp = self.fmcget(api="/devices/devicerecords")
        device_id = ""
        for device in rsp["items"]:
            if device["name"] == devicename:
                device_id = device["id"]
        if not device_id:
            errorstring = "Could not perform operation - could not finde device {}".format(devicename)
            self.log_debug(errorstring)                
            raise ValueError(errorstring)
            
        rsp = self.fmcget(api="/devices/devicerecords/" + device_id + "/physicalinterfaces")
        interface_id = ""
        for interface in rsp["items"]:
            if interface["name"] == name:
                interface_id = interface["id"]

        if not interface_id:
            errorstring = "Could not perform operation - could not find interface"
            self.log_debug(errorstring)                
            raise ValueError(errorstring)
            
        interface_put = {
            "type": "PhysicalInterface",
            "hardware": {
                "duplex": "AUTO",
                "speed": "AUTO"
            },
            "mode": "NONE",
            "enabled": True,
            "MTU": 1500,
            "managementOnly": False,
            "ifname": ifname,
            "enableAntiSpoofing": False,
            "name": name,
            "id": interface_id,
            "ipv4" : {
                "static": {
                    "address":ipv4address,
                    "netmask":ipv4mask
                }
            }
        }
        put_data = json.dumps(interface_put)
        return(self.fmcput(api="/devices/devicerecords/"+device_id+"/physicalinterfaces/"+interface_id,put_data=put_data))

        
    def add_device(self,devicename,hostname,regkey,policyname):
                
        self.log_debug("...checking if Access Policy {0} is defined on FMC".format(policyname))
        rsp = self.fmcget(api="/policy/accesspolicies")
        items = rsp["items"]

        policy_id = ""
        for item in items:
            if item["name"] == policyname:
                policy_id = item["id"]
        if not policy_id:
            self.log_debug("!!!Could not find policy {0}!".format(policyname))
            errorstring = "Could not perform operation - could not find policy"
            self.log_debug(errorstring)                
            raise ValueError(errorstring)

        device_post = {
            "name": devicename,
            "hostName": hostname,
            "regKey": regkey,
            "type": "Device",
            "license_caps": [
                "BASE",
                "MALWARE",
                "URLFilter",
                "THREAT"
            ],
            "accessPolicy": {
                "id": policy_id
            }
        }
        post_data = json.dumps(device_post)
        return(self.fmcpost(api="/devices/devicerecords",post_data=post_data))

#
# Class implementing parts of SMA API
#
class SMA(CATS):
    def __init__(self,username,password,server,port="443",debug=False,logfile=""):

        CATS.__init__(self,debug,logfile)

        self.server = server
        self.port   = port
        self.baseurl = "https://{}:{}/sma/api/v2.0".format(self.server,self.port)
        
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json',
        }
        self.device_type = "esa"
        
        b64username = (base64.b64encode(username.encode())).decode()
        b64password = (base64.b64encode(password.encode())).decode()
        bencode = base64.b64encode((username).encode())
        b64username = bencode.decode()
        bencode = base64.b64encode((password).encode())
        #b64passcode = bencode.decode()
        body = {
            "data" : {
                "userName": b64username,
                "passphrase": b64password,
                }
            }
        loginurl = "{}/login".format(self.baseurl)
        rsp = self.post(url=loginurl,headers=self.headers,data=json.dumps(body),verify=False )

        self.headers["jwtToken"] = rsp["data"]["jwtToken"]


    def reportDLPsummary(self,days="0",hours="1",minutes="0"):

        #### time format for starttime and endtime has to be like this:
        #### 2018-09-24T23:00:00.000Z
        #### minutes, seconds and millisenconds have to be zero, followed by Z
        
        time_to = datetime.utcnow().strftime('%Y-%m-%dT%H')
        time_to = time_to + ":00:00.000Z"
        time_from = (datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))).strftime('%Y-%m-%dT%H')
        time_from = time_from + ":00:00.000Z"
        
        path = "{}/reporting/mail_dlp_outgoing_traffic_summary".format(self.baseurl)
        url = "{}/?device_type={}&startDate={}&endDate={}".format(path,self.device_type,time_from,time_to)

        return (self.get(url=url,headers=self.headers,verify=False))
                
    def reportDLPpolicy(self,days="0",hours="1",minutes="0"):

        time_to = datetime.utcnow().strftime('%Y-%m-%dT%H')
        time_to = time_to + ":00:00.000Z"
        time_from = (datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))).strftime('%Y-%m-%dT%H')
        time_from = time_from + ":00:00.000Z"
        
        path = "{}/reporting/mail_dlp_outgoing_policy_detail".format(self.baseurl)
        url = "{}/?device_type={}&startDate={}&endDate={}".format(path,self.device_type,time_from,time_to)

        return (self.get(url=url,headers=self.headers,verify=False))
        
    def report(self,api,days="0",hours="1",minutes="0"):
        time_to = datetime.utcnow().strftime('%Y-%m-%dT%H')
        time_to = time_to + ":00:00.000Z"
        time_from = (datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))).strftime('%Y-%m-%dT%H')
        time_from = time_from + ":00:00.000Z"
        
        path = "{}/reporting/{}".format(self.baseurl,api)
        url = "{}/?device_type={}&startDate={}&endDate={}".format(path,self.device_type,time_from,time_to)
        return (self.get(url=url,headers=self.headers,verify=False))

    def messageTrackingDLP(self,days="0",hours="1",minutes="0",sender="",critical=True,high=True,medium=False,low=False):

        time_to = datetime.utcnow().strftime('%Y-%m-%dT%H')
        time_to = time_to + ":00:00.000Z"
        time_from = (datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))).strftime('%Y-%m-%dT%H')
        time_from = time_from + ":00:00.000Z"

        severities = ""
        if critical:
            severities = "critical"
        if high:
            if severities:
                severities = severities + ",high"
            else:
                severities = "high"
        if medium:
            if severities:
                severities = severities + ",medium"
            else:
                severities = "medium"
        if low:
            if severities:
                severities = severities + ",low"
            else:
                severities = "low"
            
        
        path = "{}/message-tracking/messages".format(self.baseurl)
        url = "{}?searchOption=messages&startDate={}&endDate={}&ciscoHost=All_Hosts".format(path,time_from,time_to)
        url = "{}&envelopeSenderfilterOperator=begins_with&envelopeSenderfilterValue={}".format(url,sender)
        if severities:
            url = "{}&dlpViolationsSeverities={}".format(url,severities)
        
        return (self.get(url=url,headers=self.headers,verify=False))

    def messageTrackingDLPdetails(self,days="0",hours="1",minutes="0",icids=[],mids=[],serialNumber=""):

        time_to = datetime.utcnow().strftime('%Y-%m-%dT%H')
        time_to = time_to + ":00:00.000Z"
        time_from = (datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))).strftime('%Y-%m-%dT%H')
        time_from = time_from + ":00:00.000Z"
        
        path = "{}/message-tracking/dlp-details/".format(self.baseurl)
        url = "{}?searchOption=messages&startDate={}&endDate={}&ciscoHost=All_Hosts".format(path,time_from,time_to)
        if serialNumber:
            url = "{}&serialNumber={}".format(url,serialNumber)
        icidquery = ""
        for icid in icids:
            if icidquery:
                icidquery = icidquery + "&" + "icid=" + str(icid)
            else:
                icidquery = "icid" + str(icid)
        if icidquery:
            url = "{}&{}".format(url,icidquery)
        midquery = ""            
        for mid in mids:
            if midquery:
                midquery = midquery + "&" + "mid=" + str(mid)
            else:
                midquery = "mid" + str(mid)
        if midquery:
            url = "{}&{}".format(url,midquery)
        if serialNumber:
            url = "{}&serialNumber={}".format(url,serialNumber)
        
        return (self.get(url=url,headers=self.headers,verify=False))

    def getDLPdetails(self,days="0",hours="1",minutes="0",sender="",critical=True,high=True,medium=False,low=False):

        data = []
        tmprsp = self.messageTrackingDLP(days=days,hours=hours,minutes=minutes,sender=sender,critical=critical,high=high,medium=medium,low=low)
        for d in tmprsp["data"]:
            mids = d["attributes"]["mid"]
            icids = d["attributes"]["allIcid"]
            serialNumber = d["attributes"]["serialNumber"]
            drsp = self.messageTrackingDLPdetails(days=days,mids=mids,icids=icids,serialNumber=serialNumber)
            data.append(drsp["data"])
        rsp = {"catsResult":"OK", "data": data}
        return(rsp)
#   Class implementing parts of SW Cloud api
#
class SWC(CATS):
    def __init__(self,baseurl,username,api_key,debug=False,logfile=""):

        CATS.__init__(self,debug,logfile)

        self.baseurl = baseurl
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': "ApiKey {}:{}".format(username,api_key),
        }


    def getAlerts(self,swcid=""):

        if swcid:
            url = "{}/api/v3/alerts/alert/{}".format(self.baseurl,swcid)                
        else:
            url = "{}/api/v3/alerts/alert/?status=open".format(self.baseurl)                
        return(self.get(url=url,headers=self.headers,verify=True))

    def getAuditLogs(self,swcid="",username=""):

        if swcid:
            url = "{}/api/v3/audit/log/{}".format(self.baseurl,swcid)                
        else:
            if username:
                url = "{}/api/v3/audit/log/?actor_name={}".format(self.baseurl,username)
            else:
                url = "{}/api/v3/audit/log/".format(self.baseurl)                
        return(self.get(url=url,headers=self.headers,verify=True))

    def getObservations(self,swcid=""):

        if swcid:
            url = "{}/api/v3/observations/all/?id={}".format(self.baseurl,swcid)
        else:
            url = "{}/api/v3/observations/all/".format(self.baseurl)            
        return(self.get(url=url,headers=self.headers,verify=True))

    def getRoles(self,swcid=""):

        if swcid:
            url = "{}/api/v3/roles/role/{}".format(self.baseurl,swcid)
        else:
            url = "{}/api/v3/roles/role".format(self.baseurl)            
        return(self.get(url=url,headers=self.headers,verify=True))

    def getFlows(self,days="0",hours="1",minutes="0"):

        url = "{}/api/v3/snapshots/session-data".format(self.baseurl)
        return(self.get(url=url,headers=self.headers,verify=True))
    

#
#   Class implementing parts of SW api
#
class SW(CATS):

    
## define structure for complex operation, first a post to initate search, then subsequent queries to see if search done, then fetch result
    API_BASE = "/sw-reporting/v1"
    API_SEARCHES = [
        {"id": "secevents","postpath":"/tenants/{0}/security-events/queries","querypath":"/tenants/{0}/security-events/queries/{1}","resultpath":"/tenants/{0}/security-events/results/{1}","comment":"show security events"},
        {"id": "topports","postpath":"/tenants/{0}/flow-reports/top-ports/queries","querypath":"/tenants/{0}/flow-reports/top-ports/queries/{1}","resultpath":"/tenants/{0}/flow-reports/top-ports/results/{1}","comment":"show Flow Reports Top Ports"},
        {"id": "topapplications","postpath":"/tenants/{0}/flow-reports/top-applications/queries","querypath":"/tenants/{0}/flow-reports/top-applications/queries/{1}","resultpath":"/tenants/{0}/flow-reports/top-applications/results/{1}","comment":"show Flow Reports Top Applications"},
        {"id": "topprotocols","postpath":"/tenants/{0}/flow-reports/top-protocols/queries","querypath":"/tenants/{0}/flow-reports/top-protocols/queries/{1}","resultpath":"/tenants/{0}/flow-reports/top-protocols/results/{1}","comment":"show Flow Reports Top Protocols"},
        {"id": "tophosts","postpath":"/tenants/{0}/flow-reports/top-hosts/queries","querypath":"/tenants/{0}/flow-reports/top-hosts/queries/{1}","resultpath":"/tenants/{0}/flow-reports/top-hosts/results/{1}","comment":"show Flow Reports Top Hosts"},
        {"id": "toppeers","postpath":"/tenants/{0}/flow-reports/top-peers/queries","querypath":"/tenants/{0}/flow-reports/top-peers/queries/{1}","resultpath":"/tenants/{0}/flow-reports/top-peers/results/{1}","comment":"show Flow Reports Top Peers"},
        {"id": "topconversations","postpath":"/tenants/{0}/flow-reports/top-conversations/queries","querypath":"/tenants/{0}/flow-reports/top-conversations/queries/{1}","resultpath":"/tenants/{0}/flow-reports/top-conversations/results/{1}","comment":"show Flow Reports Top Conversations"},
        {"id": "topservices","postpath":"/tenants/{0}/flow-reports/top-services/queries","querypath":"/tenants/{0}/flow-reports/top-services/queries/{1}","resultpath":"/tenants/{0}/flow-reports/top-services/results/{1}","comment":"show Flow Reports Top Services"},    
]        

    def __init__(self,server,username,password,debug=False,logfile=""):

        CATS.__init__(self,debug,logfile)

        self.server = server
        self.username = username
        self.password = password
        self.tenantid = ""
        self.cookie   = ""
        XSRF_HEADER_NAME = 'X-XSRF-TOKEN'
        try:
            
            url = "https://{}/token/v2/authenticate".format(self.server)
            #data = "username={}&password={}".format(self.username,self.password)
            data = {
                "username": self.username,
                "password": self.password
            }           
            self.api_session = requests.Session()
            self.log_debug("Trying to establish session to {} with username {} {}".format(self.server,self.username,self.password))
            response = self.api_session.request("POST", url, verify=False, data=data)
            if(response.status_code == 200):
                # Set XSRF token for future requests
                for cookie in response.cookies:
                    if cookie.name == 'XSRF-TOKEN':
                        self.api_session.headers.update({XSRF_HEADER_NAME: cookie.value})
                    break
                url = 'https://' + self.server + '/sw-reporting/v1/tenants/'
                rsp = self.get(url, verify=False)
                tenant_list = rsp["data"]
                self.tenantid = str(tenant_list[0]["id"])
                self.log_debug("tenantid: " + self.tenantid)
            else:
                pass 
            if not self.tenantid:
                raise RuntimeError("authentication or retrieving tenant failed")  
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                        
    
    # OVERLOADING GET FUNCTION
    def get(self,url,verify=False,headers={}):
        response = self.api_session.request("GET",url,verify)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise RuntimeError("Invalid status code {} {}".format(str(response.status_code),str(response.content))) 
        

    def post(self,url,data,headers={},verify=False):
        self.api_session.headers.update({"Content-Type":"application/json"})
        jdata = json.dumps(data)
        response = self.api_session.request("POST",url,verify=verify,data=jdata)
        if (response.status_code//100) == 2:
            return json.loads(response.content)
        else:
            raise RuntimeError("Invalid status code {} {}".format(str(response.status_code),str(response.content))) 

    def getHostGroups(self,tag=None):
      
        url = "https://{}/smc-configuration/rest/v1/tenants/{}/tags".format(self.server,self.tenantid)
        if tag:
            url = url + "/" + tag
#       url = 'https://' + SMC_HOST + '/smc-configuration/rest/v1/tenants/' + SMC_TENANT_ID + '/tags/'        

        headers = {
            "Content-Type":"application/json",
                    "Cookie": self.cookie
        }
        return (self.get(url=url,verify=False))

    def getCognitiveIncidents(self,ip):

        '''
        Cognitive Intelligence Incidents API Configuration
        The Cognitive Intelligence Incidents REST API is disabled by default. To enable the API:
        * Enable Cognitive Analytics in External Services on your SMC and Flow Collector(s).
        * Locate /lancope/tomcat/webapps/cta-events-collector/WEB-INF/classes/app.properties file on your SMC system
        * Under #CTA_ENABLED section set the cta.api.enabled option to true
        * Restart web server on your SMC system: systemctl restart lc-tomcat
        (Note: The API returns CTA incidents for all domains and expects tenantId to be 0 in the API path parameter.
        Requesting data for any specific tenant will result in error.)

        '''
                
        url = "https://{}/sw-reporting/v2/tenants/0/incidents?ipAddress={}".format(self.server,ip)
#        url = 'https://' + SMC_HOST + '/sw-reporting/v2/tenants/0/incidents?ipAddress=' + MALICIOUS_IP

        headers = {
            "Content-Type":"application/json",
                    "Cookie": self.cookie
        }
        return (self.get(url=url,headers=headers,verify=False))

    def eventList(self):      
        url = "https://{}/sw-reporting/v1/tenants/{}/security-events/templates".format(self.server,self.tenantid)
        headers = {
            "Content-Type":"application/json",
                    "Cookie": self.cookie
        }
        return (self.get(url=url,headers=headers,verify=False))
        
    
            
    def getSWpath(self,path,tag=""):

        headers = {
            "Content-Type":"application/json",
                    "Cookie": self.cookie
        }

        if self.tenantid:
            if tag:
                url = "https://{}{}{}".format(self.server,self.API_BASE,path.format(self.tenantid,tag))
#                url = "https://" + self.server  + self.API_BASE + path.format(self.tenantid,tag)
            else:
                url = "https://{}{}{}".format(self.server,self.API_BASE,path.format(self.tenantid))
        else:
            url = "https://{}{}{}".format(self.server,self.API_BASE,path)

        return (self.get(url,headers=headers,verify=False))
    
    def postSWdata(self,path,data):

        url = "https://{}{}{}".format(self.server,self.API_BASE,path)
        return (self.post(url=url,data=data,verify=False))
            
    def search(self,search,data,wait=3):
        headers = {
                    "Content-Type":"application/json",
                    "Cookie": self.cookie
        }
        found = False
        for s in self.API_SEARCHES:
            if s["id"] == search:
                postpath = s["postpath"]
                querypath = s["querypath"]
                resultpath = s["resultpath"]
                found = True
        if not found:
            self.log_debug("Illegal operation - shold not happen")
            return None

        apipath =  postpath.format(self.tenantid)

        try:
            percentcomplete = "not returned"
            rsp = self.postSWdata(apipath,data)

# insane? the parameters returned to specify job status and job id have different JSON locations"
#  --- requiring insane logig below
            if search == "secevents":
                jobstatus  = rsp["data"]["searchJob"]["searchJobStatus"]
                jobid      = rsp["data"]["searchJob"]["id"]
                percentcomplete = rsp["data"]["searchJob"]["percentComplete"]
            else:
                jobstatus  = rsp["data"]["status"]
                jobid = rsp["data"]["queryId"]
                percentcomplete = "not returned"
            self.log_debug("JOBSTATUS:" + jobstatus)
            self.log_debug("JOBID    :" + str(jobid))
            self.log_debug("PERCENT  :" + str(percentcomplete))
#        url = "https://{}{}{}".format(self.server,self.API_BASE,path)
#temp ugly below
            querypath =  querypath.format(self.tenantid,jobid)
            querypath = "https://" + self.server + self.API_BASE + querypath
            resultpath =  resultpath.format(self.tenantid,jobid)
            resultpath= "https://" + self.server + self.API_BASE + resultpath
            while True:
                time.sleep(wait)
                rsp = self.get(url=querypath,headers=headers,verify=False)
                jobstatus = rsp["data"]["status"]

                if jobstatus == "COMPLETED":
                    rsp = self.get(url=resultpath,headers=headers,verify=False)
                    return rsp

        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                    


    def searchSecurityEvents(self,days=0,hours=0,minutes=0,sourceip="",targetip="",seceventids=[],wait=3):
#
#  weird, different time format reuired for flow reports compated to security events
#       
        time_to = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        time_from = (datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))).strftime('%Y-%m-%dT%H:%M:%SZ')

        body = {
            "securityEventTypeIds": seceventids,
            "timeRange": {
            "from": time_from,
            "to": time_to
            },
        }
        if sourceip or targetip:
            hosts = []
            if sourceip:
                t = { "ipAddress": sourceip,"type":"source"}
                hosts.append(t)
            if targetip:
                t = { "ipAddress": targetip,"type":"target"}
                hosts.append(t)
            body.update({"hosts":hosts})
        rsp = self.search("secevents",body,wait)
        return rsp

    
    def searchFlowReports(self,operation,days,hours,sourceip,targetip,wait):
#
#  weird, different time format reuired for flow reports compated to security events
#

        time_to = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        temp_t = (datetime.utcnow() - timedelta(days=days,hours = hours))
        time_from = temp_t.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        body = {
            "startTime": time_from,
            "endTime": time_to,
        }
        if sourceip:
            subject = { "ipAddresses": { "includes": [sourceip],"excludes":[] } } 
            body.update({"subject":subject})
        if targetip:
            peer = { "ipAddresses": { "includes": [targetip],"excludes":[] } } 
            body.update({"peer":peer})
            
        rsp = self.search(operation,body,wait)
        return rsp

    '''

    getFlows : Search Options below
{
  "searchName": "Flows API Search on 3/1/2017 at 12:36 PM",
  "startDateTime": "2017-03-10T08:00:00Z",
  "endDateTime": "2017-03-10T08:05:00Z",
  "recordLimit": 500,
  "subject": {
    "orientation": "CLIENT",
    "ipAddresses": {
      "includes": ["192.168.0", "10.20"],
      "excludes": ["10.20.20", "192.168.0.1-100"]
    },
    "hostGroups": {
      "includes": [1234, 2345],
      "excludes": [12345, 23456]
    },
    "tcpUdpPorts": {
      "includes": ["80-9000/tcp", "67-68/udp"],
      "excludes": ["8000-9000/tcp", "68/udp"]
    },
    "username": {
      "includes": ["admin", "veep"],
      "excludes": ["jdub", "ghill"]
    },
    "byteCount": [{
      "operator": ">=",
      "value": [204800]
    }],
    "packetCount": [{
      "operator": "BETWEEN",
      "value": [100, 400]
    }],
    "macAddress": {
      "includes": ["00-1B-63-84-45-36", "00-1B-63-84-45-63"],
      "excludes": ["00-14-22-01-23-45", "00-14-22-01-23-54"]
    },
    "processName": {
      "includes": ["cmd.exe", "telnet.exe"],
      "excludes": ["ping.exe", "proc.bin"]
    },
    "processHash": {
      "includes": ["cf23df2207d99a74fbe169e3eba035e633b65d94"],
      "excludes": ["cf23df2207d99a74fbe169e3eba035e633b65d97"]
    },
    "trustSecId": {
      "includes": [32, 44],
      "excludes": [75]
    },
    "trustSecName": {
      "includes": ["CTS-One"],
      "excludes": ["CTS-Two", "CTS-Three"]
    }
  },
  "peer": {
    "ipAddresses": {
      "includes": ["2001:0db8:85a3:0000:0000:8a2e:0370:7334", "2001:DB8:0:56::/64"],
      "excludes": ["2001:DB80:0:56::ABCD:239.18.52.86", "2001:DB8:0:56:ABCD:EF12:3456:1–10"]
    },
    "hostGroups": {
      "includes": [9876, 8765],
      "excludes": [987654, 87654]
    },
    "tcpUdpPorts": {
      "includes": ["80-9000/tcp", "67-68/udp"],
      "excludes": ["8000-9000/tcp", "68/udp"]
    },
    "username": {
      "includes": ["admin", "veep"],
      "excludes": ["jdub", "ghill"]
    },
    "byteCount": [{
      "operator": ">=",
      "value": [204800]
    }],
    "packetCount": [{
      "operator": "BETWEEN",
      "value": [100, 400]
    }],
    "macAddress": {
      "includes": ["00-1B-63-84-45-36", "00-1B-63-84-45-63"],
      "excludes": ["00-14-22-01-23-45", "00-14-22-01-23-54"]
    },
    "processName": {
      "includes": ["cmd.exe", "telnet.exe"],
      "excludes": ["ping.exe", "proc.bin"]
    },
    "processHash": {
      "includes": ["cf23df2207d99a74fbe169e3eba035e633b65d94"],
      "excludes": ["cf23df2207d99a74fbe169e3eba035e633b65d97"]
    },
    "trustSecId": {
      "includes": [32, 44],
      "excludes": [75]
    },
    "trustSecName": {
      "includes": ["CTS-One"],
      "excludes": ["CTS-Two", "CTS-Three"]
    } 
  },
  "flow": {
    "tcpUdpPorts": {
      "includes": ["80-9000/tcp", "67-68/udp"],
      "excludes": ["8000-9000/tcp", "68/udp"]
    },
    "applications": {
      "includes": [3002, 3001, 116, 136],
      "excludes": [127, 125, 147, 45]
    },
    "flowDirection": "BIDIRECTIONAL",
    "byteCount": [{
        "operator": ">=",
        "value": [204800]
      }],
    "packetCount": [{
      "operator": "<=",
      "value": [10]
    }],
    "payload": {
      "includes": ["http", "blah"],
      "excludes": []
    },
    "tcpConnections": [{
        "operator": ">=",
        "value": [2000]
      }],
    "tcpRetransmissions": [{
        "operator": ">=",
        "value": [2000]
      }],
    "tlsVersion": ["TLS 1.2", "UNKNOWN"],
    "cipherSuite": {
      "messageAuthCode": ["SHA256"],
      "keyExchange": ["ECDHE"],
      "authAlgorithm": ["RSA"],
      "encAlgorithm": ["AES_128_CBC"],
      "keyLength": ["128"]

    },
    "averageRoundTripTime": [{
        "operator": "<=",
        "value": [50]
      }],
    "averageServerResponseTime": [{
        "operator": ">=",
        "value": [2000]
      }],
    "flowDataSource": [{
      "flowCollectorId": 151,
      "exporters": [{
        "ipAddress": "10.100.100.7",
        "interfaceIds": [7,27]
      },{
        "ipAddress": "10.203.1.1"
      }]
    }],
    "protocol": [114, 10],
    "includeInterfaceData": false,
    "flowAction": "permitted"
  }
}



    '''
    def getFlows(self,sip=[],shostgroup=[],pip=[],phostgroups=[],days=0,hours=1,minutes=0):
               
        url = "https://{}/sw-reporting/v2/tenants/{}/flows/queries".format(self.server,self.tenantid)

        # Set the timestamps for the filters, in the correct format, for last 60 minutes
        end_datetime = datetime.utcnow()
        start_datetime = end_datetime - timedelta(minutes=60)
        end_timestamp = end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        start_timestamp = start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Set the filter with the request data
        '''
            "peer": {
                "hostGroups": {
                    "includes": [pHostGroup]
                }
            },
        '''
        
        request_data = {
            "startDateTime": start_timestamp,
            "endDateTime": end_timestamp,
            "subject": {
                "ipAddresses": {
                    "includes": sip
                }
            },
            "peer": {
                "ipAddresses": {
                    "includes": []
                },
                "hostGroups": {
                    "includes": []
                }
            },
            
            
            "recordLimit": 50
        }
        request_data["peer"]["ipAddresses"]["includes"] = pip
        request_data["peer"]["hostGroups"]["includes"] = phostgroups
            
        headers = {'Content-type': 'application/json', 'Accept': 'application/json','Cookie':self.cookie}
        rsp = self.post(url=url,data=request_data,headers=headers,verify=False)
        self.log_debug("generating result, please wait")
        id = rsp["data"]["query"]["id"]
        url = "https://{}/sw-reporting/v2/tenants/{}/flows/queries/{}".format(self.server,self.tenantid,id)
        while rsp["data"]["query"]["percentComplete"] != 100:
            rsp = self.get(url,headers=headers,verify=False)
            time.sleep(1)

        url = "https://{}/sw-reporting/v2/tenants/{}/flows/queries/{}/results".format(self.server,self.tenantid,id)
        rsp = self.get(url,headers=headers,verify=False)        
        return(rsp)
        
class TG(CATS):

    def __init__(self,api_key,debug,logfile):
        CATS.__init__(self,debug,logfile)
        self.api_key       = api_key


    def searchTG(self,url,days=30,hours=0):
        headers = {}
        before = (datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%SZ")
        after  = (datetime.utcnow()-timedelta(days=days,hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url = "{}&before={}&after={}".format(url,before,after)

        return (self.get(url=url,headers=headers,verify=True))

    def searchDomain(self,domain,days=30,hours=0):

        url = "https://panacea.threatgrid.com/api/v2/iocs/feeds/domains?api_key={}&domain={}".format(self.api_key,domain)
        return (self.searchTG(url=url,days=days,hours=hours))

    def searchIP(self,ip,days=30,hours=0):

        url = "https://panacea.threatgrid.com/api/v2/iocs/feeds/ips?api_key={}&ip={}".format(self.api_key,ip)
        return (self.searchTG(url=url,days=days,hours=hours))

    def searchURL(self,url,days=30,hours=0):

        url = "https://panacea.threatgrid.com/api/v2/iocs/feeds/urls?api_key={}&url={}".format(self.api_key,url)
        return (self.searchTG(url=url,days=days,hours=hours))



    

class AMP(CATS):

    def __init__(self,cloud,api_client_id,api_key,debug=False,logfile=""):
        CATS.__init__(self,debug,logfile)
        self.api_client_id = api_client_id
        self.api_key       = api_key
        self.api_url = "https://api.amp.cisco.com"
        if cloud=="eu":
            self.api_url ="https://api.eu.amp.cisco.com"
        if cloud=="apjc":
            self.api_url ="https://api.apjc.amp.cisco.com"

    def apirequest(self,apicall):
    
        headers = {"ACCEPT":"application/json","Content-Type":"application/json","Authorization":""}
        bencode = base64.b64encode((self.api_client_id + ":" + self.api_key).encode())
        headers["Authorization"] = "Basic " + bencode.decode()
        if apicall.startswith("https://"):
            url = apicall
        else:
            url = self.api_url + apicall
        
        return(self.get(url=url,headers=headers,verify=False))

    def apiputrequest(self,apicall):
    
        headers = {"ACCEPT":"application/json","Content-Type":"application/json","Authorization":""}
        bencode = base64.b64encode((self.api_client_id + ":" + self.api_key).encode())
        headers["Authorization"] = "Basic " + bencode.decode()
        url = self.api_url + apicall
        
        return(self.put(url=url,headers=headers,data="",verify=False))

    def apideleterequest(self,apicall):
    
        headers = {"ACCEPT":"application/json","Content-Type":"application/json","Authorization":""}
        bencode = base64.b64encode((self.api_client_id + ":" + self.api_key).encode())
        headers["Authorization"] = "Basic " + bencode.decode()
        url = self.api_url + apicall
        
        return(self.delete(url=url,headers=headers,verify=False))
    
    def events(self,days=1,hours=0,minutes=0,detection_sha256="",application_sha256="",connector="",group="",event_type=[]):

        api_call = "/v1/events/"
        start_date = (datetime.utcnow() - timedelta(days=days,hours = hours,minutes=minutes)).strftime('%Y-%m-%dT%H:%M:%S') + "+00:00"

        query = {}
        query.update({"start_date": start_date})
        if detection_sha256:
            query.update({"detection_sha256": detection_sha256})
        if application_sha256:
            query.update({"application_sha256": application_sha256})

        querystring = urllib.parse.urlencode(query)
        api_call = api_call + "?" + querystring
        rsp = self.apirequest(api_call)
        return rsp

    def eventTypes(self):
        api_call = "/v1/event_types"
        rsp = self.apirequest(api_call)
        return rsp
        
    def computers(self,internal_ip="",external_ip="",hostname="",):

        api_call = "/v1/computers/"
        query = {}
        if internal_ip:
            query.update({"internal_ip":internal_ip})
        if external_ip:
            query.update({"external_ip":external_ip})
        if hostname:
            query.update({"hostname[]":hostname})

        querystring = urllib.parse.urlencode(query)
        api_call = api_call + "?" + querystring
        rsp = self.apirequest(api_call)
        return rsp

    def getALLcomputers(self,first=False):
        api_call = "/v1/computers/"
        if first:
            rsp = self.apirequest(api_call)
        else:
            rsp = self.apirequest(self.next_url)

        if 'next' in rsp['metadata']['links']:
            self.next_url = rsp['metadata']['links']['next']
            more = True
        else:
            more = False
        return (more,rsp)


    def computerGUID(self,guid):

        api_call = "/v1/computers/{}".format(guid)
        rsp = self.apirequest(api_call)
        return rsp

    def computerDelete(self,guid):
        api_call = "/v1/computers/{}".format(guid)
        self.apideleterequest(api_call)


    def computerTrajectory(self,guid,search=""):
### optional search par to search for ip, sha etc (like in console
###
        api_call = "/v1/computers/{}/trajectory".format(guid)
        if search:
            query = {}
            query.update({"q":search})
            querystring = urllib.parse.urlencode(query)
            api_call = api_call + "?" + querystring
            
        rsp = self.apirequest(api_call)
        return rsp

    def computerUserTrajectory(self,guid,search=""):
### optional search par to search for ip, sha etc (like in console
###
        api_call = "/v1/computers/{}/user_trajectory".format(guid)
        if search:
            query = {}
            query.update({"q":search})
            querystring = urllib.parse.urlencode(query)
            api_call = api_call + "?" + querystring
            
        rsp = self.apirequest(api_call)
        return rsp

    def computerUserActivity(self,guid,search=""):
### optional search par to search for ip, sha etc (like in console
###
        api_call = "/v1/computers/{}/user_trajectory".format(guid)
        if search:
            query = {}
            query.update({"q":search})
            querystring = urllib.parse.urlencode(query)
            api_call = api_call + "?" + querystring
            
        rsp = self.apirequest(api_call)
        return rsp

    def eventStreams(self):

        api_call = "/v1/event_streams/"
        rsp = self.apirequest(api_call)
        return rsp

    def checkHostIsolation(self,guid):

        api_call = "/v1/computers/{}/isolation".format(guid)
        rsp = self.apirequest(api_call)
        return rsp

    def startHostIsolation(self,guid):
          # Format the URL to isolate endpoint
        api_call = "/v1/computers/{}/isolation".format(guid)
        rsp = self.apiputrequest(api_call)
        return rsp

    def stopHostIsolation(self,guid):
          # Format the URL to isolate endpoint
        api_call = "/v1/computers/{}/isolation".format(guid)
        rsp = self.apideleterequest(api_call)
        return rsp

    def groups(self,groupname=""):
        api_call = "/v1/groups/"
        rsp = self.apirequest(api_call)
        return rsp

class ORBITAL(CATS):

    def __init__(self,client_id,client_password,debug=False,logfile="",cloud="us"):
        CATS.__init__(self,debug,logfile)
        self.client_id = client_id
        self.client_password = client_password
        self.api_url = "https://orbital.amp.cisco.com"
        if cloud=="eu":
            self.api_url ="https://orbital.api.eu.cisco.com"
        if cloud=="apjc":
            self.api_url ="https://orbital.api.apjc.cisco.com"

    def get_token(self):
        headers = {}
        bencode = base64.b64encode((self.client_id + ":" + self.client_password).encode())
        headers["Authorization"] = "Basic " + bencode.decode()

        #headers = {"Authorization": self.client_id + ":" + self.client_password}
        # rsp = self.get(url="{}:{}@self.api_url/v0/oauth2/token".format(self.client_id,self.client_password),headers={},verify=True)
        # data = "{}:{}".format(self.client_id,self.client_password)
        rsp = self.post(self.api_url+"/v0/oauth2/token",headers=headers,data={},verify=True)
        self.token = rsp["token"]
        self.expiry = rsp["expiry"]
       
    def stock_query(self,stock,nodes):
        headers = {"Authorization": "Bearer " + self.token,
                   'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'}

        data = {
        #  "osQuery" : [{"sql":"SELECT * FROM processes;"}],
        #    "nodes"   : ["host:VMRAT33"]
        #      "stock": "forensic-snapshot-windows-0.0.9",
        #     "nodes"   : ["ip:10.1.33.17"],
        #     "stock" : "logged_in_users"
            "name" : "catsquery",
            "interval": 0,
            "nodes": nodes,
            "stock": stock
        }
        url="/v0/query"
        rsp = self.post(url=self.api_url+url,headers=headers,data=json.dumps(data),verify=True)
       
        self.job_id = rsp["ID"]
        return (rsp)
    
    def stock_script(self,stock,nodes):
        headers = {"Authorization": "Bearer " + self.token,
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'application/json'}

        data = {
        #  "osQuery" : [{"sql":"SELECT * FROM processes;"}],
        #    "nodes"   : ["host:VMRAT33"]
        #      "stock": "forensic-snapshot-windows-0.0.9",
        #     "nodes"   : ["ip:10.1.33.17"],
        #     "stock" : "logged_in_users"
            "name" : "catsquery",
            "interval": 0,
            "nodes": nodes,
            "stock": stock
        }
        url="/v0/script/run"
        rsp = self.post(url=self.api_url+url,headers=headers,data=json.dumps(data),verify=True)
       
        self.job_id = rsp["ID"]
        return (rsp)

    def jobs(self,job_id):
        headers = {"Authorization": "Bearer " + self.token,
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'application/json'}
        url = self.api_url + "/v0/jobs/"+job_id 
        rsp = self.get(url=url,headers=headers,verify=True)
        return(rsp)
    
    def results(self,job_id):
        headers = {"Authorization": "Bearer " + self.token}
        url = self.api_url + "/v0/jobs/"+job_id + "/results"
        data = "limit=100"
        rsp = self.get(url=url,headers=headers,verify=True)

        return rsp


class UMBRELLA2(CATS):
    def __init__(self,key="",secret="",debug=False,logfile=""):
        CATS.__init__(self,debug,logfile) 
        self.token_url = "https://api.umbrella.com/auth/v2/token" 
        self.token_url = "https://{}:{}@api.umbrella.com/auth/v2/token".format(key,secret)
        self.key = key 
        self.secret = secret
        self.verify = True
        self.acquire_oauth2_token()

    def acquire_oauth2_token(self):
        headers = {}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        #    'Authorization':""
        }
        key = self.key
        secret = self.secret
        toencode = key + ":" + secret
        bencoded = base64.b64encode(toencode.encode())
        #headers["Authorization"] = "Basic " + bencoded.decode()
        data = {
            'grant_type': 'client_credentials'
        }
        rsp = self.post(url=self.token_url,headers=headers,data=json.dumps(data),verify=self.verify)
        self.access_token = rsp["access_token"]
        self.headers =  headers = {
            'Accept': 'application/json',
            'Authorization': "Bearer " + self.access_token
        }


    def admin_users(self):
        
        url = "https://api.umbrella.com/admin/v2/users"
        rsp = self.get(url=url,headers=self.headers,verify=self.verify)
        return(rsp)

    def identities(self,limit=100,offset=0):
        url = "https://api.umbrella.com/reports/v2/identities?limit={}&offset={}".format(str(limit),str(offset))
        rsp = self.get(url=url,headers=self.headers,verify=self.verify)
        return(rsp)

    def categories(self,limit=100,offset=0):
        url = "https://api.umbrella.com/reports/v2/categories?limit={}&offset={}".format(str(limit),str(offset))
        rsp = self.get(url=url,headers=self.headers,verify=self.verify)
        return(rsp)

    def reports_activity_dns(self,start="-1days",stop="now",limit="100",ip=None,identityids=None,categories=None,domains=None):
       
        '''time_to = datetime.utcnow()
        time_from = datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))
        start = str(time_from.timestamp())[:-7]
        stop = str(time_to.timestamp())[:-7]
        start = start + "000"
        stop  = stop + "000"
        print(start)
        print(stop)
        '''
        stop = "now"
        start = "-1days"
        url = "https://api.umbrella.com/reports/v2/activity/dns?from={}&to={}&limit={}".format(start,stop,limit)
        if ip:
            url = url + "&ip={}".format(ip)
        if identityids:
            url = url + "&identityids={}".format(identityids)
        if categories:
            url = url + "&categories={}".format(categories)
        if domains:
            url = url + "&domains={}".format(domains)
        rsp = self.get(url=url,headers=self.headers,verify=self.verify)
        return(rsp)


class UMBRELLA(CATS):

    def __init__(self,investigate_token="",enforce_token="",key="",secret="",mkey="",msecret="",orgid="",debug=False,logfile=""):
        CATS.__init__(self,debug,logfile)
        self.investigate_token = investigate_token
        self.enforce_token = enforce_token        
        self.key = key 
        self.secret = secret
        self.mkey = mkey
        self.msecret = msecret
        self.orgid = orgid
        

    def management_headers(self):
        headers = {}
        key = self.mkey
        secret = self.msecret
        toencode = key + ":" + secret
        bencoded = base64.b64encode(toencode.encode())
        #bencoded = base64.b64encode(toencode)
        headers["Authorization"] = "Basic " + bencoded.decode()
        #headers["Authorization"] = "Basic " + bencoded
        return (headers)

    def auth_headers(self):
        headers = {}
        key = self.key
        secret = self.secret
        toencode = key + ":" + secret
        bencoded = base64.b64encode(toencode.encode())
        #bencoded = base64.b64encode(toencode)
        headers["Authorization"] = "Basic " + bencoded.decode()
        #headers["Authorization"] = "Basic " + bencoded
        return (headers)

    def getOrganizations(self):
        headers = self.auth_headers()
        url = "https://management.api.umbrella.com/v1/organizations"
        return(self.get(headers=headers,url=url,verify=True))      
    def getDevices(self):
        headers = self.management_headers()
        url = "https://management.api.umbrella.com/v1/organizations/{}/networkdevices".format(self.orgid)
        return(self.get(headers=headers,url=url,verify=True))      

    def getDestinationLists(self):
        headers = self.management_headers()
        url = "https://management.api.umbrella.com/v1/organizations/{}/destinationlists".format(self.orgid)
        return(self.get(headers=headers,url=url,verify=True))      


    def listEnforcement(self):

        headers = {'Content-Type': 'application/json'}
        url = "https://s-platform.api.opendns.com/1.0/domains?customerKey={}".format(self.enforce_token)

        return(self.get(headers=headers,url=url,verify=True))
               
    def deleteEnforcement(self,domain):
        headers = {'Content-Type': 'application/json'}

        url = "https://s-platform.api.opendns.com/1.0/domains/{}?customerKey={}".format(domain,self.enforce_token)
        return (self.delete(url=url,headers=headers,verify=True))


    def addEnforcement(self,domain,url):
        headers = {'Content-Type': 'application/json'}
        pdata = {
            "alertTime": strftime("%Y-%m-%dT%H:%M:%S.0Z",gmtime()),
            "deviceVersion": "13.7a",
            "deviceId": "ba6a59f4-e692-4724-ba36-c28132c761de",
            "dstDomain": domain,
            "dstUrl": url,
            "eventTime": strftime("%Y-%m-%dT%H:%M:%S.0Z",gmtime()),
            "protocolVersion": "1.0a",
            "providerName": "Hacke Labrats"
        }
        url = "https://s-platform.api.opendns.com/1.0/events?customerKey={}".format(self.enforce_token)
        return(self.post(url,headers=headers,data=json.dumps(pdata),verify=True))
                  
    def report_get(self,url):
        headers = {}
        key = self.key
        secret = self.secret
        toencode = key + ":" + secret
        bencoded = base64.b64encode(toencode.encode())
        headers["Authorization"] = "Basic " + bencoded.decode()

        return(self.get(headers=headers,url=url,verify=True))

    def reportSecurityActivity(self,days=0,hours=1,minutes=0):
        # headers = {}

        time_to = datetime.utcnow()
        time_from = datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))
        start = str(time_from.timestamp())[:-7]
        stop = str(time_to.timestamp())[:-7]
        url = "https://reports.api.umbrella.com/v1/organizations/{}/security-activity?start={}&stop={}".format(self.orgid,start,stop)
#        url = "https://reports.api.umbrella.com/v1/organizations/{}/security-activity".format(self.orgid)
        return(self.report_get(url=url))

    def reportDestinationIdentities(self,domain):
    
        url = "https://reports.api.umbrella.com/v1/organizations/{}/destinations/{}/identities".format(self.orgid,domain)
        return(self.report_get(url=url))
    def reportDestinationActivity(self,domain):
    
        url = "https://reports.api.umbrella.com/v1/organizations/{}/destinations/{}/activity".format(self.orgid,domain)
        return(self.report_get(url=url))

    def investigate_get(self,url):
        headers = {
             'Authorization': 'Bearer ' + self.investigate_token
        }
        return self.get(headers=headers,url=url,verify=True)

    def investigateCategories(self,domain):
        url = "https://investigate.api.opendns.com/domains/categorization/{}/?showLabels".format(domain)
        return self.investigate_get(url=url)

    def investigateDNSDB(self,domain):
        url = "https://investigate.api.opendns.com/dnsdb/name/a/{}".format(domain)
        return self.investigate_get(url=url)

    def investigateTimeline(self,domain):
        url = "https://investigate.api.opendns.com/timeline/{}".format(domain)
        return self.investigate_get(url=url)

    def investigateIP(self,ip):
        url = "https://investigate.api.opendns.com/dnsdb/ip/a/{}".format(ip)
        return self.investigate_get(url=url)

    def investigateIPlatestDomains(self,ip):
        url = "https://investigate.api.opendns.com/ips/{}/latest_domains".format(ip)
        return self.investigate_get(url=url)

    def investigateIPtimeline(self,ip):
        url = "https://investigate.api.opendns.com/timeline/{}".format(ip)
        return self.investigate_get(url=url)

    def investigateSample(self,hash):
        url = "https://investigate.api.opendns.com/sample/{}".format(hash)
        return self.investigate_get(url=url)
  

class CTR(CATS):

    def __init__(self,client_id,client_secret,debug=False,logfile=""):
        CATS.__init__(self,debug,logfile)        
        self.client_id = client_id
        self.client_secret = client_secret
        self.debug = debug

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }

        data = {
            'grant_type': 'client_credentials'
        }
        try:
            url = 'https://visibility.amp.cisco.com/iroh/oauth2/token'
            self.log_debug("POST URL is {} Headers {} Data {} auth is {}".format(url,str(headers),str(data),client_id + "  " + client_secret))
            response = requests.post(url, headers=headers, data=data, auth=(client_id, client_secret))
    
            if response.status_code == 200:
                rsp_dict = json.loads(response.text)
                self.access_token = (rsp_dict['access_token'])
                self.scope = (rsp_dict['scope'])
                self.expiration_time = (rsp_dict['expires_in'])
                self.headers = {
                    'Authorization': 'Bearer ' + self.access_token,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                return None
            else:
                errorstring = "Access token request failed, status code: {response.status_code}"
                self.log_debug(errorstring)
                raise ValueError(errorstring)
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                    

    ''' Given raw text, return structured observables'''
    def get_observables(self,raw_text):

        data = json.dumps({"content":raw_text})
        return (self.post('https://visibility.amp.cisco.com/iroh/iroh-inspect/inspect', headers=self.headers, data=data,verify=True))

    ''' Given observables, enrich with verdict/judgeent '''
    def enrich_observables(self,observables):
        enrich_url = 'https://visibility.amp.cisco.com/iroh/iroh-enrich/deliberate/observables'
        data = json.dumps(observables)
        return (self.post(enrich_url, headers=self.headers, data=data,verify=True))

    ''' Given observables, what actions can be performed by different modules (e.g isolate host, AO etc '''        
    def get_actions_for_observables(self,observables): 

        # grab the type of the observable, that is needed
#        rsp= self.get_observables(observable)
#        type_of_observable = rsp[0]['type']        

#        data = json.dumps([{"value":observable, "type":type_of_observable}])
        data = json.dumps(observables)
        return (self.post('https://visibility.amp.cisco.com/iroh/iroh-response/respond/observables', headers=self.headers, data=data,verify=True))


    def get_observe_observables(self,observables):
        
        data = json.dumps(observables)
        return (self.post('https://visibility.amp.cisco.com/iroh/iroh-enrich/observe/observables', headers=self.headers, data=data,verify=True))
    
    def get_sightings_for_observables(self,observables):
       
        otype = observables[0]["type"]
        ovalue = observables[0]["value"]
        return (self.get('https://private.intel.amp.cisco.com/ctia/{}/{}/sightings'.format(otype,ovalue), headers=self.headers,verify=True))
    

    def create_casebook(self,casebook_name,casebook_title,casebook_description,observables_string):
        # timenow = datetime.utcnow()
        d = date.today()
        start_date = d.strftime("%Y-%m-%d")
        casebook_obj_json = {}
        casebook_obj_json["type"] = "casebook"
        casebook_obj_json["title"] = casebook_name + " " +  start_date
        casebook_obj_json["texts"] = []
        if observables_string:
            observables = json.loads(observables_string)
        else:
            observables = []
        casebook_obj_json["observables"] = observables
        casebook_obj_json["short_description"] = "short description..."
        casebook_obj_json["description"] = casebook_description
        casebook_obj_json["schema_version"] = "1.0.11"

        casebook_obj_json["timestamp"] = start_date

        casebook_obj_json["source"] = "ao"

        casebook_obj_json["tlp"] = "amber"
       
        data = json.dumps(casebook_obj_json)
        return (self.post('https://private.intel.amp.cisco.com/ctia/casebook', headers=self.headers, data=data,verify=True))
     
    def get_casebook(self,id):
        id = urllib.parse.quote(id,safe='')

        url = "https://private.intel.amp.cisco.com/ctia/casebook/{}".format(id)
        return self.get(headers=self.headers,url=url,verify=True)

    def delete_casebook(self,id):
        id = urllib.parse.quote(id,safe='')
        bearer_token = 'Bearer ' + self.access_token
        headers = {
            'Authorization': bearer_token,
#            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        url = "https://private.intel.amp.cisco.com/ctia/casebook/{}".format(id)
        return self.delete(headers=self.headers,url=url,verify=True)
        
    def add_casebook_observables(self,id,observables_string):
        observables = json.loads(observables_string)
        
        observables_update = {"operation": "add",
                "observables": observables
               }
        data = json.dumps(observables_update)
        id = urllib.parse.quote(id,safe='')
        url = "https://private.intel.amp.cisco.com/ctia/casebook/{}/observables".format(id)
        return (self.post(url, headers=self.headers, data=data,verify=True))
    
    def create_incident(self,incident_info):
        url = 'https://private.intel.amp.cisco.com/ctia/incident'
        data = json.dumps(incident_info)
        return(self.post(url,headers=self.headers,data=data,verify=True))
                         

class ISE_ANC(CATS):
    
    def __init__(self,server,username,password,debug,logfile=""):
        CATS.__init__(self,debug,logfile)
        self.server = server
        self.username = username
        self.password = password


    def get_putdata(self,ip,mac,policy):
    
        putdata = {"OperationAdditionalData" : {"additionalData" : []} }
        if ip:
            t = {}
            t["name"] = "ipAddress"
            t["value"]= ip
            putdata["OperationAdditionalData"]["additionalData"].append(t)
        if mac:
            t = {}
            t["name"] = "macAddress"
            t["value"]= mac
            putdata["OperationAdditionalData"]["additionalData"].append(t)
        if policy:
            t = {}
            t["name"] = "policyName"
            t["value"]= policy
            putdata["OperationAdditionalData"]["additionalData"].append(t)
        return putdata


    
    def activeSessions(self):

### active sessions only available via xml :-(
        
        headers = {"ACCEPT":"application/xml"}
        url = "https://" +self.username + ":" + self.password + "@" + self.server + "/admin/API/mnt/Session/ActiveList"
        active_sessions = {}
        sessions = []
        try:
            r = requests.get(url,verify=False,headers=headers)
            status_code = r.status_code
            if  (status_code / 100) == 2:
                root = ET.fromstring(r.text)
                for s in root.iter("activeSession"):
                    tstr = {"user_name":"","calling_station_id":"","framed_ip_address":"","framed_ipv6_address":""}
                    for e in s.iter():
                        for key in tstr:
                            if e.tag == key:
                                tstr[key] = e.text

                    sessions.append(tstr)

                active_sessions.update({"sessions":sessions})
                active_sessions.update({"rtcResult":"OK"})
                return active_sessions
            else:
                errorstring = "Error in get " + str(status_code)
                raise ValueError(errorstring)
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                                

    def endpoints(self,eid=""):
        headers = {"ACCEPT":"application/json","ERS-Media-Type":"identity.internaluser.1.2"}
        headers = {"ACCEPT":"application/json","Content-Type":"application/json"}

        url = "https://" + self.username + ":" + self.password + "@" + self.server + ":9060/ers/config/ancendpoint"
        if eid:
            url = url + "/" + eid

        return (self.get(url=url,headers=headers,verify=False))

    def endpoints2(self,eid=""):
        headers = {"ACCEPT":"application/json","Authorization":""}
        bencode = base64.b64encode((self.username + ":" + self.password).encode())
        headers["Authorization"] = "Basic " + bencode.decode()
        url = "https://" + self.server + "/api/v1/endpoint?size=100&page=4"
        return(self.get(url=url,headers=headers,verify=False))
    

    def macPolicy(self,mac=""):
        rsp = self.endpoints()
        resources = rsp["SearchResult"]["resources"]
        macs = []
        rsp = {"catsresult":"OK"}
        for item in resources:
            r1 = self.endpoints(item["id"])
            thismac = r1["ErsAncEndpoint"]["macAddress"]
            thispolicy = r1["ErsAncEndpoint"]["policyName"]
            if mac:
                mac = mac.upper()
                if mac==thismac:
                    rsp.update({"mac": thismac, "policy":thispolicy})
                    return rsp
                else:
                    pass
            else:
                macs.append({"mac": thismac, "policy":thispolicy})
        rsp.update({"macs":macs})
        return rsp
            
    def applyPolicy(self,ip,mac,policy):
        headers = {"ACCEPT":"application/json","Content-Type":"application/json"}
        mac = mac.upper()
        putdata = json.dumps(self.get_putdata(ip,mac,policy))
        url = "https://" + self.username + ":" + self.password + "@" + self.server + ":9060/ers/config/ancendpoint/apply"

        return (self.put(url=url,headers=headers,data=putdata,verify=False))

    def clearPolicy(self,ip="",mac=""):
        mac = mac.upper()
        headers = {"ACCEPT":"application/json","Content-Type":"application/json"}

        putdata = json.dumps(self.get_putdata(ip,mac,""))
        url = "https://" + self.username + ":" + self.password + "@" + self.server + ":9060/ers/config/ancendpoint/clear"
        return (self.put(url=url,headers=headers,data=putdata,verify=False))


    def listPolicies(self):
        headers = {"ACCEPT":"application/json","Content-Type":"application/json"}

        url = "https://{}:{}@{}:9060/ers/config/ancpolicy".format(self.username,self.password,self.server)
        return (self.get(url=url,headers=headers,verify=False))

class ISE_PXGRID(CATS):

    '''
    pxGrid auth with either client certs or passwords
    
    A. PASSWORD BASED
      
    A1. i = cats.ISE_PXGRID(server,nodename)     // create account
    A2. i.activate()                             // activate account
    A3. Manually approve account in ISE PXGRID GUI
    A4. password = i.getPassword()               // save the auto generated password, if you want to use again without haaving to manually approve
    A5. rsp = i.getSessions()                    // perform operation on pxgrid, e.g. getSessions...
    -----
    ----- if you want to run another program you don't have t redo the whole process with manaual activation
    -----
    A6. i = cats.ISE_PXGRID(server,nodename,password)  // where password is what you saved in step A3
    A7. rsp = i.getSessions()                    // 
       retrieve password and use for all other basic pxgrid ops (not using pxgrid where you need to use the secret)


    B. CERTIFICATE BASED

    B1. i = cats.ISE_PXGRID(server,nodename,clientcert,clientkey,clientkeypassword,servercert)   // create account
    B2. i.activate()                                                                             // activate account
    B3. Manually approve account in ISE, or have ISE configured to accept cert authenticated nodes automatically
    B4. rsp = i.getSessions()                  // perform operation on pxgrid, e.g. getSessions...


    -----
    ----- if you want to run another program with the same activated nodename you don't have t redo the whole process without calling i.activate
    -----
    B5. i = cats.ISE_PXGRID(server,nodename,clientcert,clientkey,clientkeypassword,servercert)   // create account
    B6. rsp = i.getSessions()
    '''
    
    
    def __init__(self,server,nodename,password="",clientcert="",clientkey="",clientkeypassword="",servercert="",description="",debug=False,logfile=""):
        CATS.__init__(self,debug,logfile)
        self.server = server
        self.nodename = nodename
        self.password = password        
        self.clientcert = clientcert
        if clientcert:
            self.authwithclientcert = True
            
        self.clientkey  = clientkey        
        self.clientkeypassword  = clientkeypassword
        self.servercert  = servercert
        self.description = description
        pdata = {
            "nodeName": self.nodename
        }
        
        if not clientcert and not password:
            '''
            We have pxGrid with password auth but do not have a password yet, Create Account, retrieve username password
            '''            
            url = "https://{}:8910/pxgrid/control/AccountCreate".format(self.server)
            headers = {'Content-Type': 'application/json','Accept':'application/json'}
            rsp = self.post(url=url,headers=headers,data=json.dumps(pdata),verify=False)
            self.pxpassword = rsp["password"]
            self.password  =  self.pxpassword
            self.pxusername = rsp["userName"]
            if self.pxusername != self.nodename:
                self.log_debug("NODENAME AND PX USERNAME DIFFERERENT")
                return

    def activate(self):
        
        self.authstring = self.getAuthstring(self.nodename,self.password)
        self.log_debug("nodenae" + self.nodename)                
        self.log_debug("pass" + self.password)        
        self.log_debug("auths" + self.authstring)
        self.log_debug("desc" + self.description)
        self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}

        attempts = 0
        activated = False
        while (not activated and attempts < 5):
            pdata = {
                "description": self.description
            }
            url = "https://{}:8910/pxgrid/control/AccountActivate".format(self.server)
            rsp = self.post(url=url,headers=self.headers,data=json.dumps(pdata),verify=False)
            attempts = attempts +1
            accountstate = rsp["accountState"]
            if accountstate == 'ENABLED':
                self.activated = True
                break
            else:
                if attempts > 5:
                    raise ValueError("pxGrid Account not actrivated.... waited 5 minutes, quitting")
                time.sleep(60)
            
    
    def serviceLookup(self,servicename):
        self.authstring = self.getAuthstring(self.nodename,self.password)
        self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
        pdata = {'name':servicename}
        url = "https://{}:8910/pxgrid/control/ServiceLookup".format(self.server)
        rsp = self.post(url=url,headers=self.headers,data=json.dumps(pdata),verify=False)
        self.service = rsp['services'][0]
        self.restBaseURL = rsp['services'][0]["properties"]["restBaseUrl"]
        self.peerNodeName = self.service["nodeName"]

    def updateAccessSecret(self):
        pdata = {
            "peerNodeName": self.service["nodeName"]
        }
        self.authstring = self.getAuthstring(self.nodename,self.password)
        self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
        url = "https://{}:8910/pxgrid/control/AccessSecret".format(self.server)
        rsp = self.post(url=url,headers=self.headers,data=json.dumps(pdata),verify=False)
        self.secret = rsp["secret"]
        self.log_debug(self.secret)
        
    def getAuthstring(self,username,password):
        toencode = username + ":" + password
        bencoded = base64.b64encode(toencode.encode())
        return(bencoded.decode())

    def getPassword(self):
        return self.password

    def isActivated(self):
        return self.activated
    
    def getSessions(self,ip="",mac=""):

        try:

            self.serviceLookup("com.cisco.ise.session")
            self.updateAccessSecret()
            
            if ip:
                payload = '{ "ipAddress": "%s" }' % ip
                url = self.restBaseURL  + "/getSessionByIpAddress"
            else:
                if mac:
                    mac = mac.upper()
                    payload = '{ "macAddress": "%s" }' % mac
                    url = self.restBaseURL + "/getSessionByMacAddress"
                else:
                    payload = '{}'
                    url = self.restBaseURL+ "/getSessions"                    

            self.authstring = self.getAuthstring(self.nodename,self.secret)
            self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
            
            return(self.post(url=url,headers=self.headers,data=payload,verify=False))

            
            
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                


    def getBindings(self):

        try:
            self.serviceLookup("com.cisco.ise.sxp")
            self.updateAccessSecret()
            self.authstring = self.getAuthstring(self.nodename,self.secret)
            self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
#            self.restBaseURL = "https://ise70.labrats.se:8910/pxgrid/ise/sxp"            
            payload = '{}'
            url = self.restBaseURL+ "/getBindings"                    
            
            return(self.post(url=url,headers=self.headers,data=payload,verify=False))

            
            
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                            

    def getSecurityGroups(self):

        try:
            self.serviceLookup("com.cisco.ise.config.trustsec")
            self.updateAccessSecret()
            self.authstring = self.getAuthstring(self.nodename,self.secret)
            self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
#            self.restBaseURL = "https://ise70.labrats.se:8910/pxgrid/ise/sxp"            
            payload = '{}'
            url = self.restBaseURL+ "/getSecurityGroups"                    
            
            return(self.post(url=url,headers=self.headers,data=payload,verify=False))

            
            
        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                            

    def getSecurityGroupACLs(self):

        try:
            self.serviceLookup("com.cisco.ise.config.trustsec")
            self.updateAccessSecret()
            self.authstring = self.getAuthstring(self.nodename,self.secret)
            self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
#            self.restBaseURL = "https://ise70.labrats.se:8910/pxgrid/ise/sxp"            
            payload = '{}'
            url = self.restBaseURL+ "/getSecurityGroupAcls"                    
            
            return(self.post(url=url,headers=self.headers,data=payload,verify=False))

        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                            

    def getProfiles(self):

        try:
            self.serviceLookup("com.cisco.ise.config.profiler")
            self.updateAccessSecret()
            self.authstring = self.getAuthstring(self.nodename,self.secret)
            self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
#            self.restBaseURL = "https://ise70.labrats.se:8910/pxgrid/ise/sxp"            
            payload = '{}'
            url = self.restBaseURL+ "/getProfiles"                    
            
            return(self.post(url=url,headers=self.headers,data=payload,verify=False))

        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err                                                            
        
            
    def getFailures(self):

        try:
            self.serviceLookup("com.cisco.ise.radius")
            self.updateAccessSecret()
            self.authstring = self.getAuthstring(self.nodename,self.secret)
            self.headers = {'Content-Type': 'application/json','Accept':'application/json','Authorization':"Basic {}".format(self.authstring)}
#            self.restBaseURL = "https://ise70.labrats.se:8910/pxgrid/ise/sxp"            
            payload = '{}'
            url = self.restBaseURL+ "/getFailures"                    

            return(self.post(url=url,headers=self.headers,data=payload,verify=False))

        except Exception as err:
            raise RuntimeError(self.exception_string(err)) from err       

class DUO_ADMIN(CATS):

    
    def get_duo_headers(self,path,params):

        """
        Return HTTP Basic Authentication ("Authorization" and "Date") headers.
        method, host, path: strings from request
        params: dict of request parameters
        skey: secret key
        ikey: integration key
        """
        print("ikey" + self.api_ikey)
        print("skey" + self.api_skey)
        # create canonical string
        method = "GET"
        now = email.utils.formatdate()
        canon = [now, method.upper(), self.duo_host.lower(), path]
        args = []
        for key in sorted(params.keys()):
            val = params[key]
            if isinstance(val, str):
                val = val.encode("utf-8")
                args.append('%s=%s' % (urllib.parse.quote(key, '~'), urllib.parse.quote(val, '~')))
                canon.append('&'.join(args))
                canon = '\n'.join(canon)

        # sign canonical string
        sig = hmac.new(codecs.encode(self.api_skey,'latin-1'), codecs.encode(str(canon)), hashlib.sha1)
        auth = '%s:%s' % (self.api_ikey, sig.hexdigest())

        headers = {"Date": now,
                   "Authorization":'Basic %s' % base64.b64encode(codecs.encode(auth)).decode('utf-8'),
                   "Host":self.duo_host,
                   "Accept":"application/json"}
        return (headers)
    
    def encode_headers(self,params):
        """ encode headers """
        encoded_headers = {}
        for k, v in params.items():
            if isinstance(k, six.text_type):
                k = bytes(k.encode())
            if isinstance(v, six.text_type):
                v = v.encode('ascii')
            encoded_headers[k] = v
        return encoded_headers        

    def merge_two_dicts(self,x, y):
        """Given two dicts, merge them into a new dict as a shallow copy."""
        z = x.copy()
        z.update(y)
        return z

    def sign(self, method, host, path, params):
        """
        Return HTTP Basic Authentication ("Authorization" and "Date") headers.
        method, host, path: strings from request
        params: dict of request parameters
        skey: secret key
        ikey: integration key
        """
        if self.debug:
            self.log_debug("Signing method {} host {} path {} params {} skey {} ikey {}".format(method,host,path,json.dumps(params),self.api_skey,self.api_ikey))
        # create canonical string
        now = email.utils.formatdate()
        canon = [now, method.upper(), host.lower(), path]
        args = []
        for key in sorted(params.keys()):
            val = params[key]
            #if isinstance(val, unicode):
            #    val = val.encode("utf-8")
            args.append(
            	'%s=%s' % (urllib.parse.quote(key, '~'), urllib.parse.quote(val, '~')))
        canon.append('&'.join(args))
        canon = '\n'.join(canon)
        # sign canonical string
        if self.debug:
            self.log_debug("signing canon:\n{}".format(canon))
        
        sig = hmac.new(self.api_skey.encode(), canon.encode(), hashlib.sha1)
        auth = '%s:%s' % (self.api_ikey, sig.hexdigest())

        # return headers
        return {'Date': now, 'Authorization': 'Basic %s' % base64.b64encode(auth.encode()).decode()}

    def __init__(self,api_ikey,api_skey, duo_host, debug,logfile):
        CATS.__init__(self,debug,logfile)
        self.api_ikey= api_ikey
        self.api_skey= api_skey
        self.duo_host= duo_host
        self.duo_headers = {'Content-Type':'application/x-www-form-urlencoded', 
                            'User-Agent': 'Duo API Python/4.2.3',
                            'Host':self.duo_host}
        self.log_debug("\r\nInitiating Duo with api_ikey: {} api_skey: {} host: {}".format(self.api_ikey,self.api_skey,self.duo_host))
        
        """ necessary headers for Duo """
        self.duo_headers = {'Content-Type':'application/x-www-form-urlencoded',
        'User-Agent': 'Duo API Python/4.2.3','Host':self.duo_host}

        self.service_url = "/admin/v1/users"
        """ necessary headers for Duo """

        # Duo check API request  
        """ THIS IS AUTH API request, no ADMIN API
        service_url ="/auth/v2/check"
        params={ }
        params1= self.sign("GET", self.duo_host, service_url, params, self.api_skey, self.api_ikey)
        params2= self.merge_two_dicts(self.duo_headers, params1)
        encoded_headers = self.encode_headers(params2)
        try:
            response = requests.get("https://"+duo_host+service_url, headers=encoded_headers)
            if response.status_code == 200:
                self.log_debug("\r\nDuo access initiated, status code: "+ str(response.status_code))
                return None    
            else:
                self.log_debug("\r\nAccess token request failed, status code: "+ str(response.status_code))
                return None
        except Exception as err:
            return self.exception_refuse_init(err)

        """
        return None






    def integrations(self):
        service_url = "/admin/v1/integrations"
        params = {}
    
        headers = {}
        headers = self.get_duo_headers(path=service_url,params=params)
        
        response=self.get(url="https://"+self.duo_host+service_url, headers=headers,verify=False)
        return(response)
    
    def logs(self, days=1,hours=0,minutes=0, users=""):

            time_to = datetime.utcnow()
            time_from = datetime.utcnow() - timedelta(days=int(days),hours = int(hours),minutes=int(minutes))

            dt_time_to = time_to.replace().timestamp()
            dt_time_to= re.sub(r'\d+$', '', str(dt_time_to))
            dt_time_from = time_from.replace().timestamp()
            dt_time_from= re.sub(r'\d+$', '', str(dt_time_from))
            dt_time_to = dt_time_to[:-1] + "000"
            dt_time_from = dt_time_from[:-1] + "000"

            mintime = dt_time_from
            maxtime = dt_time_to
            self.log_debug("\r\nGet the Duo logs request with api_ikey: {} api_skey: {} host: {} mintime: {} maxtime: {}".format(self.api_ikey,self.api_skey,self.duo_host, mintime, maxtime))
            # Duo check API request  
            service_url ="/admin/v2/logs/authentication"
            if users:
                params={ 'mintime':str(mintime), 'maxtime':str(maxtime), 'users':str(users) }
            else:
                params={ 'mintime':str(mintime), 'maxtime':str(maxtime) }
            params1= self.sign("GET", self.duo_host, service_url, params)
            params2= self.merge_two_dicts(self.duo_headers, params1)
            encoded_headers = self.encode_headers(params2)

            #print("params:",params)
            try:
                #response = requests.get("https://"+self.duo_host+service_url, params= params, headers=encoded_headers)
                #print("response1:",response.content)


                response=self.get(url="https://"+self.duo_host+service_url+'?mintime='+str(mintime)+'&maxtime='+str(maxtime)+'&users='+str(users), headers=encoded_headers,verify=False)
                #print("####response2:",response)
                #print("####")

                self.log_debug("\r\nDuo logs requested, status code: ")
                return response   

            except Exception as err:
                raise RuntimeError(self.exception_string(err)) from err                            

    def getAuthLogs(self,username="",days=7,hours=0,minutes=0):
        rsp1 = self.users(username=username)
        user_id = rsp1["response"][0]["user_id"]
        return (self.logs(users=user_id,days=days,hours=hours,minutes=minutes))

    
    def users(self, username):
            self.log_debug("\r\nGet the Duo users request") 
            # Duo check API request  
            service_url ="/admin/v1/users"

            params={ 'username':str(username) }
            params1= self.sign("GET", self.duo_host, service_url, params)
            params2= self.merge_two_dicts(self.duo_headers, params1)
            encoded_headers = self.encode_headers(params2)

           
            try: 


                response=self.get(url="https://"+self.duo_host+service_url+'?username='+str(username), headers=encoded_headers,verify=False)
                #print("####response2:",response)
                #print("####", response.status_code)


                self.log_debug("\r\nDuo users requested, status code: ")
                return response  

            except Exception as err:
                raise RuntimeError(self.exception_string(err)) from err                                            


    def userCreate(self,username, email):
        if email == None or email == "<no value>":
            post_data = {"username": username, "status": "active"}
        else:
    	    post_data = {"username": username, "email":email,"status": "active"}

        service_url = "/admin/v1/users"

        params1= self.sign("POST", self.duo_host, service_url, post_data)
        params2= self.merge_two_dicts(self.duo_headers, params1)
        encoded_headers = self.encode_headers(params2)
#        rsp =self.post(url="https://"+self.duo_host+service_url, headers=encoded_headers, data=json.dumps(post_data),verify=True)
        rsp =self.post(url="https://"+self.duo_host+service_url, headers=encoded_headers, data=post_data,verify=True)
        return(rsp)



    def userEnroll(self,username, email):
        if email == None or email == "<no value>":
            self.log_debug("ERROR: no email address.")
            return None
        #POST /admin/v1/users/enroll
        service_url_enroll ="/admin/v1/users/enroll"
        post_data = {"username": username, "email":email}
        params1= self.sign("POST", self.duo_host, service_url_enroll, post_data)
        params2= self.merge_two_dicts(self.duo_headers, params1)
        encoded_headers = self.encode_headers(params2)
        rsp=self.post(url="https://"+self.duo_host+service_url_enroll, headers=encoded_headers, data=post_data,verify=False)
        return(rsp)

    def modify_user(self,id,status):
        service_url_enroll ="/admin/v1/users/{}".format(id)
        post_data = {"status":status}
        params1= self.sign("POST", self.duo_host, service_url_enroll, post_data)
        params2= self.merge_two_dicts(self.duo_headers, params1)
        encoded_headers = self.encode_headers(params2)
        rsp=self.post(url="https://"+self.duo_host+service_url_enroll, headers=encoded_headers, data=post_data,verify=False)
        return(rsp)
        

class WEBEX(CATS):

    def __init__(self,roomid,token,debug=False,logfile=""):
        CATS.__init__(self,debug,logfile)
        self.roomid = roomid
        self.token = token
        self.debug = debug

    def postmessage(self,message,markdown):

        headers = {
                    "Content-type":"application/json",
                    "Accept":"application/json",
                    "Authorization":"Bearer " + self.token
                   }
        
        url = "https://webexapis.com" + "/v1/messages"
        data = {
            "roomId": self.roomid,
            "markdown": markdown,
        }

        rsp = self.post(url=url,headers=headers,data=json.dumps(data),verify=True)

class AAD(CATS):
    def __init__(self,tenant,client_id,client_secret,debug=False,logfile=""):
        CATS.__init__(self,debug,logfile)
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant = tenant
        url = "https://login.microsoftonline.com/{}/oauth2/v2.0/token".format(self.tenant)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
            }
        scope = "https://graph.microsoft.com/.default"
        grant_type = "client_credentials"
        data = "client_id={}&scope={}&client_secret={}&grant_type={}".format(client_id,scope,client_secret,grant_type)
        rsp = self.post(url=url,headers=headers,data=data,verify=True)
    
        self.access_token = rsp["access_token"]

    
    
    def getGroupsAndRolesByUPN(self,upn):
        url = "https://graph.microsoft.com/v1.0/users/{}/memberOf".format(upn)
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(self.access_token)
        }
        rsp = self.get(url=url,headers=headers,verify=True)
        return(rsp)
    
    def getRoles(self):
        url = "https://graph.microsoft.com/v1.0/directoryRoles"
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(self.access_token)
        }
        rsp = self.get(url=url,headers=headers,verify=True)
        return(rsp)
    

    