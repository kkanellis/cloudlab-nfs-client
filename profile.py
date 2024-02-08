"""
NFS client connecting to an NFS server (running on a different experiment),
using a shared VLAN (created by the NFS server experiment).
"""

import ipaddress

import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Only Ubuntu images supported.
imageList = [
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD', 'UBUNTU 22.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD', 'UBUNTU 20.04'),
]

# Do not change these unless you change the setup NFS script too. 
nfsLanName = "nfsLan"

# Number of NFS clients (there is always a server)
pc.defineParameter("nodeCount", "Number of Nodes",
    portal.ParameterType.INTEGER, 1)

pc.defineParameter("osImage", "Select OS image",
    portal.ParameterType.IMAGE,
    imageList[0], imageList)

# Optional physical type for all nodes.
pc.defineParameter("phystype", "Optional physical node type",
    portal.ParameterType.STRING, "",
    longDescription="Specify a single physical node type (pc3000,d710,etc) " +
                    "instead of letting the resource mapper choose for you.")

# Shared VLAN params
pc.defineParameter("sharedVlanName", "Shared VLAN Name",
    portal.ParameterType.STRING,"kkanellis-nfs-tiering",
    advanced=True,
    longDescription="A shared VLAN name (functions as a private key allowing other experiments to connect to this node/VLAN). "
                    "Must be fewer than 32 alphanumeric characters.")

pc.defineParameter("sharedVlanNetwork", "Shared VLAN Network",
    portal.ParameterType.STRING, "10.254.254.0/24",
    advanced=True,
    longDescription="Set the shared VLAN network, as a CIDR.")

# Always need this when using parameters
params = pc.bindParameters()

if params.phystype != "":
    tokens = params.phystype.split(",")
    if len(tokens) != 1:
        pc.reportError(portal.ParameterError("Only a single type is allowed", ["phystype"]))

pc.verifyParameters()

# Represent given network
network = ipaddress.IPv4Network(unicode(params.sharedVlanNetwork))
netmask = network.netmask
hosts = network.hosts()
gateway = next(hosts)

# The NFS network. All these options are required.
nfsLan = request.LAN(nfsLanName)

# Create nodes and attached to the NFS lan.
for i in range(params.nodeCount):
    node = request.RawPC("node%d" % i)
    node.hardware_type = params.phystype
    node.disk_image = params.osImage

    # Setup the client to use the shared VLAN
    iface = node.addInterface()
    iface.addAddress(
        pg.IPv4Address(next(hosts).compressed, netmask.compressed))

    nfsLan.addInterface(iface)
    nfsLan.connectSharedVlan(params.sharedVlanName)

    # Initialization script for the clients
    node.addService(
        pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)