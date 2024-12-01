#!/bin/bash
set -e

echo "Please enter your Azure Resource Group:"
read rg
echo "Please enter the public IP from which you are accessing lab:"
read myip
echo "Your resource group is $rg and you public ip is $myip."
read -p "Do you want to continue? (y/n): " answer

if [[ "$answer" != "y" ]]; then
    echo "Exiting..."
    exit 1
fi

vmpassword="@zureC1sco1!"
vmadmin="vmadmin"
vnetname="SERVERVNET"
vnetprefix="10.0.0.0/16"
subnetname="default"
subnetprefix="10.0.0.0/24"
region="swedencentral"
nsg="myNSG"
vm1="VM1"
vm2="VM2"
PublicIPname="PublicIP"
PublicLB="PublicLB"

echo "get the cloud-init.yaml"
wget https://raw.githubusercontent.com/drnop/az700training/refs/heads/main/cloud-init.yaml

echo "creating resource group"
az group create -n $rg -l $region

echo "creating vnet"
az network vnet create \
  --resource-group $rg \
  --name $vnetname \
  --location $region \
  --address-prefix $vnetprefix \
  --subnet-name $subnetname \
  --subnet-prefix $subnetprefix

echo "creating nsg"
az network nsg create \
    --resource-group $rg \
    --name $nsg \
    --location $region

echo "creating nsg rules"
az network nsg rule create \
  --resource-group $rg \
  --nsg-name $nsg \
  --name AllowHTTP \
  --priority 110 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefix $myip \
  --destination-port-range 80

az network nsg rule create \
  --resource-group $rg \
  --nsg-name $nsg \
  --name AllowSSH \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefix $myip \
  --destination-port-range 22

echo "updating subnet with nsg"
  az network vnet subnet update \
  --name $subnetname \
  --resource-group $rg \
  --vnet-name $vnetname\
  --network-security-group $nsg

echo "creating VM1"
az vm create \
  --resource-group $rg \
  --name $vm1\
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username $vmadmin \
  --admin-password $vmpassword \
  --location $region \
  --vnet-name $vnetname \
  --subnet $subnetname \
  --public-ip-address "" \
  --nsg $nsg \
  --custom-data @cloud-init.yaml  

echo "getting IP of VM1"
vm1ip=$(az vm list-ip-addresses \
  --resource-group $rg \
  --name $vm1 \
  --output tsv \
  --query "[0].virtualMachine.network.privateIpAddresses[0]")

echo "creating VM2"
az vm create \
  --resource-group $rg \
  --name $vm2\
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username $vmadmin \
  --admin-password $vmpassword \
  --location $region \
  --vnet-name $vnetname \
  --subnet $subnetname \
  --public-ip-address "" \
  --nsg $nsg \
  --custom-data @cloud-init.yaml

echo "getting IP of VM2"
vm2ip=$(az vm list-ip-addresses \
  --resource-group $rg \
  --name $vm2 \
  --output tsv \
  --query "[0].virtualMachine.network.privateIpAddresses[0]")

echo "creating public ip"
az network public-ip create \
  --resource-group $rg \
  --name $PublicIPname \
  --allocation-method Static \
  --sku Standard

echo "Create load balancer"
az network lb create \
  --resource-group $rg \
  --name $PublicLB \
  --sku Standard \
  --location $region \
  --public-ip-address $PublicIPname \
  --frontend-ip-name FrontendConfiguration
#  --backend-pool-name BackendPool \

echo "create address pool"
az network lb address-pool create \
  --resource-group $rg \
  --lb-name $PublicLB \
  --vnet $vnetname \
  --name MyAddressPool

echo "add addresses to address pool"
az network lb address-pool address add \
 --resource-group $rg \
 --lb-name $PublicLB \
 --name VM1IP \
 --vnet $vnetname \
 --pool-name MyAddressPool \
 --ip-address $vm1ip

az network lb address-pool address add \
 --resource-group $rg \
 --lb-name $PublicLB \
 --name VM2IP \
 --vnet $vnetname \
 --pool-name MyAddressPool \
 --ip-address $vm2ip

echo "create health probe"
az network lb probe create \
 --lb-name $PublicLB \
 --resource-group $rg \
 --name MyHealthProbe \
 --protocol http \
 --port 80 \
 --path /

echo "create lb rule"
az network lb rule create \
 --lb-name $PublicLB  \
 --resource-group $rg \
 --name MyLBrule \
 --protocol tcp \
 --frontend-port 80 \
 --backend-port 80 \
 --backend-pool-name MyAddressPool \
 --probe MyHealthProbe

#
# Creating Azure objects for FMC and GWLB
#
fwvnet="FWVNET"
fwvnetprefix="172.16.0.0/16"
fwmgmtsubnet="ManagementSubnet"
fwmgmtsubnetprefix="172.16.0.0/24"
fwoutsidename="outside"
fwoutsideprefix="172.16.1.0/24"
fwinsidename="inside"
fwinsideprefix="172.16.2.0/24"
GWLB="GWLB"
frontendip="172.16.1.200"
frontendname="myFrontEnd"

echo "creating Firewall vnet and subnets"
az network vnet create \
  --resource-group $rg \
  --name $fwvnet \
  --address-prefix $fwvnetprefix \
  --subnet-name $fwmgmtsubnet \
  --subnet-prefix $fwmgmtsubnetprefix

az network vnet subnet create \
  --resource-group $rg \
  --name $fwoutsidename \
  --vnet-name $fwvnet \
  --address-prefix $fwoutsideprefix

az network vnet subnet create \
  --resource-group $rg \
  --name $fwinsidename \
  --vnet-name $fwvnet \
  --address-prefix $fwinsideprefix


echo "Creating Gateway Load Balancer"
az network lb create \
  --name $GWLB \
  --resource-group $rg \
  --sku Gateway \
  --vnet-name $fwvnet \
  --subnet $fwoutsidename \
  --frontend-ip-name $frontendname

  #--private-ip-address $GWLBstaticIP

az network lb frontend-ip update  \
  --lb-name $GWLB\
  --name $frontendname\
  --resource-group $rg\
  --private-ip-address $frontendip

echo "create address pool"
az network lb address-pool create \
  --resource-group $rg \
  --lb-name $GWLB \
  --vnet $fwvnet \
  --name FWpool

echo "create GWLB health probe"
az network lb probe create \
 --lb-name $GWLB \
 --resource-group $rg \
 --name GWLBhealthprobe \
 --protocol tcp \
 --port 9443 

exit

#echo "create GWLB lb rule MANUALLY instead!
#az network lb rule create \
# --lb-name $GWLB  \
# --resource-group $rg \
# --name fwLBrule \
# --backend-pool-name FWpool \
# --protocol All\
# --probe GWLBhealthprobe \
# --frontend-port 0\
# --backend-port 0


