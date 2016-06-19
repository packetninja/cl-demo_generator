#!/usr/bin/env python

########
#
# Demo generator
#
# Creates a Vagrant file from a topology.dot file and a basic management setup for a Cumulus Linux based network.
#
# Written by Attilla de Groot, idea based on Eric Pulvino's Topology Converter (credits, kudos etc.)
#
#    Changelog:
#   v0.1 -- 2016-03-29: Basic script commit 
#   v0.2 -- 2016-03-31: Bug fixes, node arguments, added ebgp-vxlan demo
#   v0.3 -- 2016-04-05: Readme files, code comment, directory structure
#
#
#
#######


#
# Python modules. Importing pydotplus for furture graph generation.
#

import pydotplus
import pprint
import sys
import re
from pygraphviz import *
from random import randrange

#
# Global vars that are used in the script
#

topology_file=sys.argv[1] #accept our topology file as input
vagrantconfig="./Vagrantfile" #Set our vagrantfile output. Existing VAGRANTFILES will be overwritten
ansiblevars="./provisioning/group_vars/all"

#
# Main function 
#

def main():
    inventory = parse_topology(topology_file)
    inventory = add_mac(inventory)
    gen_ansible_template(inventory)
    gen_virtualbox_vagrant(inventory)

def parse_topology(topology_file):
    #
    # Using pygraphiz to parse the topology file and create a dict for all the VM host information.
    #

    topology = AGraph(topology_file)
    
    #
    # Creating empty dict and filling it with the node variables
    #

    inventory = {}
    for node in topology.nodes():
        if node not in inventory:
            inventory[node] = {}
            inventory[node]['interfaces'] = {}
        inventory[node]['type'] = node.attr['type']
        inventory[node]['function'] = node.attr['function']
        inventory[node]['os'] = node.attr['os']

    #
    # For each edge add a network and create two interfaces (one for head, one for tail) and add these interfaces to the same network to create connectivity
    #

    net = 1
    for edge in topology.edges():
        if edge.attr['tailport'] not in inventory[edge[0]]['interfaces']:
            inventory[edge[0]]['interfaces'][edge.attr['tailport']] = {}  
        inventory[edge[0]]['interfaces'][edge.attr['tailport']]['network'] = "network"+str(net)
 
        if edge.attr['headport'] not in inventory[edge[1]]['interfaces']:
            inventory[edge[1]]['interfaces'][edge.attr['headport']] = {}  
        inventory[edge[1]]['interfaces'][edge.attr['headport']]['network'] = "network"+str(net)
        net += 1
   
    return inventory 

def add_mac(inventory):
    #
    # Vagrant creates eth0 by default for management purposes. This is also the default management port when CL is running on a bare metal switch.
    #
    # To ceate a network that matches a real-world scenario, interfaces have to be renamed. This is done using udev rules and static mac-addresses. This function generates a random mac address for each interface. This also includes the vagrant interface, because this is the first interface for the VM and has to be unique in the network (e.g. LNV ID's are based on this) 
    for device in inventory:
        random1 = randrange(100000,999999)
        vagrantmac = "000000"+str(random1)
        inventory[device]['interfaces']['vagrant'] = {}
        inventory[device]['interfaces']['vagrant']['macaddress'] = vagrantmac 
        for interface in inventory[device]['interfaces']:
            random2 = randrange(100000,999999)
            umac = "000000"+str(random2)
            inventory[device]['interfaces'][interface]['macaddress'] = umac
    return inventory

def gen_ansible_template(inventory):
    #
    # This function generates ansible variables to setup the basic management environment. 
    #
    # - Vars for udev rules file
    # - Vars for management interface
    # - Vars for oob-switch
    #   
    ansible_vars = open(ansiblevars,"w")
    ansible_vars.write("\nheader_tmpl: |+\n #\n #Configured by Ansible\n #\n\n")
    
    ansible_vars.write("udev:\n")
    for device in inventory:
        ansible_vars.write("  "+device+":\n    interfaces:\n")
        for interface in inventory[device]['interfaces']:
            mac = inventory[device]['interfaces'][interface]['macaddress']
            newmac = mac[0:2]+':'+mac[2:4]+':'+mac[4:6]+':'+mac[6:8]+':'+mac[8:10]+':'+mac[10:12]
            ansible_vars.write("      "+interface+": \""+newmac+"\"\n")
    ansible_vars.write("dhcp:\n")
    lastoctet = 101
    for device in inventory:
        if "eth0" in inventory[device]['interfaces']:
            ansible_vars.write("  "+device+":\n")
            for interface in inventory[device]['interfaces']:
                if interface == "eth0":
                    mac = inventory[device]['interfaces'][interface]['macaddress']
                    newmac = mac[0:2]+':'+mac[2:4]+':'+mac[4:6]+':'+mac[6:8]+':'+mac[8:10]+':'+mac[10:12]
                    ansible_vars.write("    mac: \""+newmac+"\"\n")
                    ansible_vars.write("    lastoctet: \""+str(lastoctet)+"\"\n")
            lastoctet += 1
    ansible_vars.write("interfaces:\n")
    for device in inventory:
        if inventory[device]['type'] == "switch" and inventory[device]['function'] == "oob":        
            ansible_vars.write("  "+device+":\n")
            for interface in inventory[device]['interfaces']:
                if device != "vagrant":
                    ansible_vars.write("    "+interface+": \"\"\n")
    ansible_vars.close()

def gen_virtualbox_vagrant(inventory):
    #
    # This function create the Vagrant file by using the variables in the dict. Differences are made based on the node types (e.g. memory and OS type).
    #
    vagrantfile = open(vagrantconfig,"w")
    vagrantfile.write("Vagrant.configure(\"2\") do |config|\n")
    vagrantfile.write("   config.vm.provider \"virtualbox\" do |v|\n")
    vagrantfile.write("       v.gui=false\n")
    vagrantfile.write("   end\n")

    for device in inventory:
        vagrantfile.write("   config.vm.define \""+device+"\" do |vx|\n")
        vagrantfile.write("       vx.vm.hostname = \""+device+"\"\n")
        vagrantfile.write("       vx.vm.synced_folder \".\", \"/vagrant\", disabled: true\n")
       
        if inventory[device]['type'] == "server": 
            vagrantfile.write("       vx.vm.provider \"virtualbox\" do |v|\n")
            vagrantfile.write("           v.name = \""+device+"\"\n")
            vagrantfile.write("           v.memory = \"400\"\n")
            vagrantfile.write("       end\n")
            vagrantfile.write("       vx.vm.box = \"boxcutter/debian82\"\n")
            vagrantfile.write("       vx.vm.provision \"ansible\" do |ansible|\n")
            vagrantfile.write("           ansible.playbook = \"provisioning/main.yml\"\n")
            vagrantfile.write("       end\n")
        else:
            vagrantfile.write("       vx.vm.provider \"virtualbox\" do |v|\n")
            vagrantfile.write("           v.name = \""+device+"\"\n")
            vagrantfile.write("           v.memory = \"300\"\n")
            vagrantfile.write("       end\n")
            vagrantfile.write("       vx.vm.box = \"CumulusCommunity/VX-3.0\"\n")
            vagrantfile.write("       vx.vm.provision \"ansible\" do |ansible|\n")
            vagrantfile.write("           ansible.playbook = \"provisioning/main.yml\"\n")
            vagrantfile.write("       end\n")

        #
        # Generated mac-addresses are set on the specific interfaces
        #

        for interface in inventory[device]['interfaces']:
            if interface != "vagrant":
                mac = inventory[device]['interfaces'][interface]['macaddress']
                network = inventory[device]['interfaces'][interface]['network']
                vagrantfile.write("       vx.vm.network \"private_network\", virtualbox__intnet: \""+network+"\", auto_config: false, mac: \""+mac+"\"\n")
        
        #
        # Alle SWP interfaces need to be configured in promisc mode. The address of the vagrant mac-address is set here.
        #
        net = 2
        vagrantfile.write("       vx.vm.provider \"virtualbox\" do |vbox|\n")
        for interface in inventory[device]['interfaces']:
            if interface == "vagrant":
                vagrantmac = inventory[device]['interfaces'][interface]['macaddress']
                vagrantfile.write("           vbox.customize [\"modifyvm\", :id, \"--macaddress1\", \""+vagrantmac+"\"]\n")  
            else:
                vagrantfile.write("           vbox.customize ['modifyvm', :id, \"--nicpromisc"+str(net)+"\", 'allow-vms']\n")
                net += 1                
        vagrantfile.write("       end\n")
        vagrantfile.write("   end\n")
    vagrantfile.write("end\n")
    vagrantfile.close()

main()
