import Pyro4
import socket
import sys
import yasnac.remote.erc as erc

sys.excepthook = Pyro4.util.excepthook

def main() :

    # Need to get local ip address in order to bind the pyro daemon..
    # socket.gethostbyname(socket.gethostname()) gives 127.0.0.1.
    # So do the gross thing
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("sudoroom.org", 80))
    localipaddr = s.getsockname()[0]
    s.close()
    
    robot = erc.ERC()
    Pyro4.config.SERIALIZER = "pickle"
    Pyro4.config.SERIALIZERS_ACCEPTED = {"json","marshal","serpent","pickle"}
    Pyro4.Daemon.serveSimple(
        {
            robot: "sudoroom.robot.yasnac"
        },
        host = localipaddr,         
        ns = False )

if __name__== "__main__" :
    main()