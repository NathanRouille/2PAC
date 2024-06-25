##############         IMPORTS         ##############
#####################################################


##############         CLASSES         ##############
#####################################################
class Config:
    def __init__(self, name, num_nodes, cluster_addr, cluster_port, other_param1, cluster_addr_with_ports, other_param2, pub_key_map, priv_key, pub_poly, share, some_flag, batch_size, round):
        self.name = name
        self.MaxPool = num_nodes
        self.clusterAddr = cluster_addr
        self.clusterPort = cluster_port
        self.other_param1 = other_param1
        self.clusterAddrWithPorts = cluster_addr_with_ports
        self.other_param2 = other_param2
        self.pub_key_map = pub_key_map
        self.priv_key = priv_key
        self.pub_poly = pub_poly
        self.share = share
        #self.log_level = log_level                 #Je l'enleve dans Node
        self.IsFaulty = some_flag
        self.batch_size = batch_size
        self.round = round

    def __repr__(self):
        return f"Config(name={self.name}, num_nodes={self.num_nodes}, cluster_addr={self.cluster_addr}, " \
               f"cluster_port={self.cluster_port}, other_param1={self.other_param1}, " \
               f"cluster_addr_with_ports={self.cluster_addr_with_ports}, other_param2={self.other_param2}, " \
               f"pub_key_map={self.pub_key_map}, priv_key={self.priv_key}, pub_poly={self.pub_poly}, " \
               f"share={self.share}, log_level={self.log_level}, some_flag={self.some_flag}, " \
               f"batch_size={self.batch_size}, round={self.round})"


#############         FUNCTIONS         #############
#####################################################


##############         EXEMPLES         #############
#####################################################


################         MAIN         ###############
#####################################################
