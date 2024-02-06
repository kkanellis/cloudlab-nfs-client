
import geni.portal as portal
import geni.rspec.pg as pg
import geni.rspec.emulab as emulab

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Number of NFS clients (there is always a server)
pc.defineParameter("nodeCount", "Number of Nodes",
                   portal.ParameterType.INTEGER, 1)

# Only Ubuntu images supported.
imageList = [
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD', 'UBUNTU 22.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD', 'UBUNTU 20.04'),
]

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   imageList[0], imageList)

# Optional physical type for all nodes.
pc.defineParameter("phystype", "Optional physical node type",
                   portal.ParameterType.STRING, "",
                   longDescription="Specify a single physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

# Shared VLAN params
pc.defineParameter(
    "sharedVlanName", "Shared VLAN Name",
    portal.ParameterType.STRING,"kkanellis-nfs-tiering",
    advanced=True,
    longDescription="A shared VLAN name (functions as a private key allowing other experiments to connect to this node/VLAN). Must be fewer than 32 alphanumeric characters."),

pc.defineParameter(
    "sharedVlanAddress", "Shared VLAN IP Address",
    portal.ParameterType.STRING, "10.254.254.1",
    advanced=True,
    longDescription="Set the IP address for the shared VLAN interface.  Make sure to use an unused address within the subnet of an existing shared vlan!"),

pc.defineParameter(
    "sharedVlanNetmask", "Shared VLAN Netmask",
    portal.ParameterType.STRING, "255.255.255.0",
    advanced=True,
    longDescription="Set the subnet mask for the shared VLAN interface, as a dotted quad.")


# Always need this when using parameters
params = pc.bindParameters()

if params.phystype != "":
    tokens = params.phystype.split(",")
    if len(tokens) != 1:
        pc.reportError(portal.ParameterError("Only a single type is allowed", ["phystype"]))

pc.verifyParameters()

# The NFS network. All these options are required.
nfsLan = request.LAN(nfsLanName)
nfsLan.best_effort = True
nfsLan.vlan_tagging = True
nfsLan.link_multiplexing = True

# Create nodes and attached to the NFS lan.
for i in range(params.nodeCount):
    node = request.RawPC("node%d" % i)
    node.hardware_type = params.phystype
    node.disk_image = params.osImage

    # Setup the client to use the shared VLAN
    iface = node.addInterface()
    iface.addAddress(
        pg.IPv4Address(params.sharedVlanAddress, params.sharedVlanNetmask))

    nfsLan.addInterface(iface)
    nfsLan.connectSharedVlan(params.sharedVlanName)

    # Initialization script for the clients
    node.addService(
        pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)