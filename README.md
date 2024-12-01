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
   

