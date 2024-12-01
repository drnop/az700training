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

![FWVNET and subnets.](pngs/FWVNETsubnets.png)

The topology of FWVNET is shown in picture below. We have a Gateway Load Balancer - more about that later- and also subnets ManagementSubnet and outside. We will add FMC to the ManagementSubnet. The FTDs will have one interface in the ManagementSubnet (for management by FMC) and the data interface GigabitEthernet0/0 will be in the outside subnet. The script has also created an inside subnet but that will not be needed because the design is based on VXLAN, allowing all traffic to enter via the outside interface.

![FWVNET topology.][pngs/FWVNETtopology.png)


