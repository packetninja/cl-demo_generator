##Cumulus Demo generator

Cumulus networks has a virtual machine available with Cumulus Linux, the OS that runs on bare-metal switches. With this virtual machine you can test functionalities of the operating system without having access to physical hardware. 

This demo topology generator uses Vagrant, Ansible and Graphviz .dot topologies to generate a virtual network of Cumulus VX's and server nodes to simulate a real-world network. It can be used to test automation tools, get an understanding of the OS and its functionalities or even recreate a production enviroment and prepare a rollout. 

If you would like to create a more complex or large network, you should use the official topology generator that is available on the following URL. In general it is advisable to contact Cumulus if you want to use either of the tools to make sure you get the correct experience.
https://github.com/CumulusNetworks/topology_converter


### Usage

## Clone the project

git clone https://github.com/packetninja/cumulus-demo.git
cd ./cumulus-demo

## Install Dependencies

Depending on your operating system, you need to have the following Python modules installed:

- Pygraphviz, pydotplus

To run a demo environment, you should have Vagrant and Ansible installed as well.


## Generate the Vagrantfile with:

Create your topology file according to the documentation in the topology directory. Run the demo script with the dot file as argument:

./demo.py ./topologies/cumulus-reference/reference_topology.dot


## Start the demo topology

Always start the oob-server and oob-switch before the other virtual machines. Thise makes sure that the cumulus ZTP runs correctly. Keep in mind that a topology with a large number of hosts needs a host with better specifications (a vx uses 200mb memory, "server" 400).

- vagrant up oob-mgmt-server oob-mgmt-switch
- vagrant up

ssh into your management server and jumphost and manage your virtual network.
- vagrant ssh oob-mgmt


## Project todo
- Add generation of hosts file on oob-mgmt server
- Use Jinja to create Vagrantfile and ansible var files instead of writing to files.
