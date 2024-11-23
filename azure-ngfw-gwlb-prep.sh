rg="HACKE"
myip="176.10.137.180"
vmadmin="vmadmin"
vmpassword="@teaAzureTra1ning"
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

wget https://raw.githubusercontent.com/drnop/az700training/refs/heads/main/cloud-init.yaml
az group create -n $rg -l $region

az network vnet create \
  --resource-group $rg \
  --name $vnetname \
  --location $region \
  --address-prefix $vnetprefix \
  --subnet-name $subnetname \
  --subnet-prefix $subnetprefix

az network nsg create \
    --resource-group $rg \
    --name $nsg \
    --location $region

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

  az network vnet subnet update \
  --name $subnetname \
  --resource-group $rg \
  --vnet-name $vnetname\
  --network-security-group $nsg

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

vm1ip=$(az vm list-ip-addresses \
  --resource-group $rg \
  --name $vm1 \
  --output tsv \
  --query "[0].virtualMachine.network.privateIpAddresses[0]")

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

vm2ip=$(az vm list-ip-addresses \
  --resource-group $rg \
  --name $vm2 \
  --output tsv \
  --query "[0].virtualMachine.network.privateIpAddresses[0]")

az network public-ip create \
  --resource-group $rg \
  --name $PublicIPname \
  --allocation-method Static \
  --sku Standard

#Create load balancer
az network lb create \
  --resource-group $rg \
  --name $PublicLB \
  --sku Standard \
  --location $region \
  --public-ip-address $PublicIPname \
  --frontend-ip-name FrontendConfiguration
#  --backend-pool-name BackendPool \

az network lb address-pool create \
  --resource-group $rg \
  --lb-name $PublicLB \
  --vnet $vnetname \
  --name MyAddressPool

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

az network lb probe create \
 --lb-name $PublicLB \
 --resource-group $rg \
 --name MyHealthProbe \
 --protocol http \
 --port 80 \
 --path /

az network lb rule create \
 --lb-name $PublicLB  \
 --resource-group $rg \
 --name MyLBrule \
 --protocol tcp \
 --frontend-port 80 \
 --backend-port 80 \
 --backend-pool-name MyAddressPool \
 --probe MyHealthProbe


