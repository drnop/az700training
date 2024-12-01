#!/usr/bin/python3
import sys
import getopt
import cats
import json

def debug_print(rsp,debug=False):
        if debug:
                print(json.dumps(rsp,indent=4,sort_keys=True))
       
def main(argv):
        # default values - can be overridden at command line with -d and -f filename
        debug = False
        credsfile = "creds.json"
        # default valules
        myDeviceGroup = "AutoScaleDeviceGroup"
        myOutsideZone = "OutsideZone"
        myVNIZone = "VNIzone"
        myPolicy  = "MyAccessPolicy"
        myRule    = "MyAccessPolicyRule"
        healthProbeSource = "168.63.129.16"
        myHealthProbePort = 9443
        myPlatformPolicy = "Platform Policy"
        try:
                opts, args = getopt.getopt(argv,"df:")
                for opt, arg in opts:
                        if opt == ("-d"):
                                debug = True
                        if opt == ("f"):
                                credsfile=arg
        except Exception as err:
                print("Invalid option specified")
                
        creds = json.loads(open(credsfile).read())
        fmcserver = creds["ip"]
        username = creds["username"]
        password = creds["password"]

        fmc = cats.FMC(fmcserver,username,password,debug,"")
        
        print("Creating Device Group {}".format(myDeviceGroup))
        rsp =fmc.createDeviceGroup(name=myDeviceGroup)
        debug_print(rsp,debug)

        # rsp = fmc.createHostObject(name=myHealthProbe,value="168.63.129.16",objecttype="host")

        print("Creating Security Zones {} and {}".format(myOutsideZone,myVNIZone))
        rsp =fmc.createSecurityZone(name=myOutsideZone,interfacemode="ROUTED")
        debug_print(rsp,debug)
        rsp =fmc.createSecurityZone(name=myVNIZone,interfacemode="ROUTED")
        debug_print(rsp,debug)

        print("Creating Access Policy {}".format(myPolicy))
        rsp = fmc.createAccessPolicy(name=myPolicy)
        debug_print(rsp,debug)
       
        print("Creating Access Policy Rule {} for src and dest {}".format(myRule,myVNIZone))
        rsp = fmc.createAccessPolicyRule(policyName=myPolicy,ruleName=myRule,sourceZone=myVNIZone,destinationZone=myVNIZone)
        debug_print(rsp,debug)

        print("Creating Platform Policy {}".format(myPlatformPolicy))
        rsp = fmc.createPlatformPolicy(name=myPlatformPolicy)
        debug_print(rsp,debug)
       
        print("Creating Platform HTTP Settings for allowing port {} from IP {}".format(myHealthProbePort,healthProbeSource,zone=myOutsideZone))
        rsp = fmc.createPlatformHTTPsetting(platformPolicy=myPlatformPolicy,port=myHealthProbePort,networkobject=healthProbeSource,zone=myOutsideZone)
        debug_print(rsp,debug)
        
       
       
                
if __name__ == "__main__":
    main(sys.argv[1:])
    
