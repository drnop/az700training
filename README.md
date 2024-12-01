# Inserting Cisco Secure Firewall FTD in Azure with GWLB

## Introduction

This lab shows how to use service chaining with an Azure Gateway Load balancer in Azure to protect a web site.

You will need access to an azure subscription and the rights to create necessary objects in a resource group.

Prerequisite knowledge includes
* some understanding of Azure Networking (VNETs, subnets, routing, load balancers...)
* some understanding of Cisco Secure Firewall (FTD) managed  by Cisco Firepower Management Center (FMC)
* some understanding of Azure CLI

The topology is shown in figure below.

![Overall Topology](pngs/topology.png)

All resources shown in azure should be  created in the student's Azure resource group. At a high level we note that we have two different VNETs.
* SERVERVNET where we define the public load balancer that distributes the traffic between Azure VMs VM1 and VM2 in the default subnet. We also have a public IP associated with the public load balancer so we can test the connection.
* FWVNET where we will define the Gateway Load Balancer (GWLB) that will load balance traffic over the firewalls that will add services such as access rules with IPS, Anti-Malware, Reputation filtering and more.

The student accesses all the lab with an internet routable internet (student public IP).

## Initial Setup using Cloudshell with bash script

Take note of the Azure Resource Group that is allocated by the lab proctor, the resource group must be unique in the lab environment subscription.

Find out the public IPv4 address that you use when connecting to the internet, for example using a site such as [What is My IP](https://www.whatismyip.com/).

1. **Login to the Azure Portal.**
2. **Open a Cloudshell with Bash.**

   ![Cloud shell (bash).](pngs/cloudshell.png)
   
4. **In cloudshell, use wget to retrieve the setupscript.**

   wget raw.githubusercontent.com/drnop/az700training/refs/heads/main/azure-ngfw-gwlb-prep.sh
   

6. **In cloudshell execute the script file**

   bash azure-ngfw-gwlb-prep.sh
   
   This should prompt you for your unique Azure Resource Group, your public IP address and the passwords used to create the VMs.

   (The passwords for the VMs are required at creation, but typically you would not need to use the passwords to login to the VMs).

8. **The setup will take a couple of minutes. Rest!**

9. **When the setup script has completed, inspect the resources created in the Azure Portal.**

VNET SERVERNET with a default subnet has been created
Public Load Balancer PLB has been created
VM1 and VM2 have been created.
A public IP named PublicIP has been created, what is the value of the IP address?

![Resources created by script.](pngs/scriptresources.png)

10. **Test that you can access the public IP with your browser using http**

Note: HTTPS has not been setup on the server, so ensure you use HTTP.

Note: Access to the server has been restricted by an NSG to only allow your public IP entered in the setup script.

![Our fantastic web application.](pngs/hello.png)

We now have create a fantastic web application which is load balanced with a public load balancer. Our mission now is to insert Cisco Secure Firewall to secure this environment. We will do so without changing the topology in this VNET and in a way which supports autoscaling.

## Adding Cisco Secure Firewall: FMC

We will now add Cisco Secure Firewalls. This is done in a separate VNET, FWVNET, that could potentially be in a different region or even subscription. The FWVNET has already been created by the script as shown in picture below. You may want to make a note of the IP prefixes of the ManagementSubnet and outside subnets.

![FWVNET and subnets.](pngs/FWNETsubnets.png)

The topology of FWVNET is shown in picture below. We have a Gateway Load Balancer - more about that later- and also subnets ManagementSubnet and outside. We will add FMC to the ManagementSubnet. The FTDs will have one interface in the ManagementSubnet (for management by FMC) and the data interface GigabitEthernet0/0 will be in the outside subnet. The script has also created an inside subnet but that will not be needed because the design is based on VXLAN, allowing all traffic to enter via the outside interface.

![FWVNET topology.](pngs/FWNETtopology.png)

1. **Find Cisco Firepower Management Center 300 in the Marketplace and click create**

![FMCv in Marketplace](pngs/FMCvMarketplace.png)

2. **FMC Resource Group, Region and Credentials**

![FMC resource groups, region and credentials.](pngs/fmccreate1.png)

Important: Use your Resource Group and Region where you created your previous resources.

Note that you have two sets of admin credentials, one for accessing the FMC VM and one for accessing the FMC web GUI. 
For NTP you can give pool.ntp.org or any valid public NTP server.

Important: You will need the FMC web GUI credentials later!


4. **FMC VNET and subnet**

![FMC VNET and subnet.](pngs/fmccreate2.png)

Important: Use the FWVNET and the ManagementSubnet.

5. **Create the FMC**

This will take some time. A good time for coffee or a smoke. Or for learning how to smoke if you don't already.

6. **Modify NSG attached to FMC interface to allow inbound access from your public IP**

By default access access to FMC is closed. In Azure portal, find the NSG and modify the incoming rules so you can access the FMC via HTTPS form your PC.

![FMC modification of NSG to allow for HTTPS from your poublic IP](pngs/fmcnsg.png)

7. **Access the FMC via the Web GUI and turn on evaluation license**

Find the FMC public IP and point your web browser to it with https://. Turn on evaluation licensing.

![Find FMC public IP.](pngs/fmcpip.png)

![Turn on Eval license](pngs/fmclicense.png)

9. **Add a user to FMC to allow for API access**

We will use REST APIs to configure FMC.

Add an API user by navigating to users menu. Ensure you note down the username and pasword and give the user the Administrator Role.

![Add API user/](pngs/fmcapiuser.png)

10. **Access the Scripting host**

This could be any system with python3 installed. If your PC fulfills the requirements you can use it. Otherwise, ask the proctor for access to a machine.

11. **Prepare the creds.json file**

    The script reads a file creds.json which constains information to access the FMC via the API.
    Create a file with the following format called creds.json, but modify the IP of the FMC and the credentials to suit your environment.

    {"ip":"my ip address",
    "username":"apiuser",
    "password":"xxxxxxxx"}

12. ""Download cats.py setupfmc.py to the Scripting host**

    





