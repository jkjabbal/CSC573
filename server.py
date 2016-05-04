import socket,threading
import sys


PORT = 7734
BUFFER_SIZE = 1024

peerlist = []
rfclist = []

class P2S(threading.Thread):
    def __init__(self,peer_info):
        threading.Thread.__init__(self)
        self.conn=peer_info[0]
        self.addr=peer_info[1]

    def run(self):
        while 1:
            data = self.conn.recv(BUFFER_SIZE)
            if data.startswith("EXIT"): break
            if not data: break
            self.parse_request(data)
        self.remove_peer_record(data)

    def parse_request(self,req):
        self.verify_request(req)
        if self.status_code==200:
            req_list = req.split('\r\n')
            if not (req_list[1].lstrip('Host: '),req_list[2].lstrip('Port: ')) in peerlist :
                peerlist.append((req_list[1].lstrip('Host: '),req_list[2].lstrip('Port: ')))
            if req.startswith('ADD'):
                self.add_rfc(req)
            self.send_response(req)
        else :
            response="P2P-CI/1.0 "+str(self.status_code)+" "+self.status_reason
            self.conn.send(response)

    def verify_request(self,req):
        self.status_code=0
        self.status_reason=""
        req_list=req.split('\r\n')
        if "P2P-CI/1.0" not in req_list[0] :
            self.status_code=505
            self.status_reason="P2P-CI Version Not Supported"
        elif not ((req_list[0].startswith("ADD") or req_list[0].startswith("LOOKUP") or req_list[0].startswith("LIST")) and (req_list[1].startswith("Host: ") and req_list[2].startswith("Port: "))):
            self.status_code=400
            self.status_reason="Bad Request"
        elif not req_list[0].startswith("LIST"):
            if not req_list[len(req_list)-1].startswith("Title: "):
                self.status_code=400
                self.status_reason="Bad Request"
            else :
                self.status_code=200
                self.status_reason="OK"
        else :
            self.status_code=200
            self.status_reason="OK"

    def add_rfc(self,req):
        req_list = req.split('\r\n')
        if (req_list[0].lstrip('ADD RFC ').rstrip(' P2P-CI/1.0'),req_list[len(req_list)-1].lstrip('Title: '),req_list[1].lstrip('Host: ')) not in rfclist :
            rfclist.append((req_list[0].lstrip('ADD RFC ').rstrip(' P2P-CI/1.0'),req_list[len(req_list)-1].lstrip('Title: '),req_list[1].lstrip('Host: '),req_list[2].lstrip('Port: ')))

    def send_response(self,req):
        response=""
        req_list = req.split('\r\n')
        if req_list[0].startswith('ADD'):
            response=response+"P2P-CI/1.0 "+str(self.status_code)+" "+self.status_reason
            response=response+"\r\n"+req_list[0].lstrip('ADD ').rstrip('P2P-CI/1.0')+req_list[len(req_list)-1].lstrip('Title: ')+req_list[1].lstrip('Host:')+req_list[2].lstrip(
                'Port:')
        elif req_list[0].startswith('LIST'):
            response=response+"P2P-CI/1.0 "+str(self.status_code)+" "+self.status_reason
            response_list=rfclist
            for (rfc_number,rfc_title,hostname,port) in response_list:
                response=response+"\r\n"+"RFC "+rfc_number+" "+rfc_title+" "+hostname+" "+str(port)
        elif req_list[0].startswith('LOOKUP'):
            response_list=self.handle_lookup(req_list)
            if len(response_list) == 0 :
                self.status_code=404
                self.status_reason="Not Found"
                response=response+"P2P-CI/1.0 "+str(self.status_code)+" "+self.status_reason
            else :
                response=response+"P2P-CI/1.0 "+str(self.status_code)+" "+self.status_reason
                for (rfc_number,rfc_title,hostname,port) in response_list:
                    response=response+"\r\n"+"RFC "+rfc_number+" "+rfc_title+" "+hostname+" "+str(port)
        self.conn.send(bytes(response))

    '''def handle_list(self):
        response_list=[]
        for (rfc_number,rfc_title,hostname) in rfclist :
            for (peer_hostname,peer_port) in peerlist:
                if peer_hostname==hostname :
                    response_list.append((rfc_number,rfc_title,hostname,peer_port))
        return response_list'''

    def handle_lookup(self,req_list):
        response_list=[]
        for(rfc_number,rfc_title,hostname,peer_port) in rfclist :
            if (rfc_number == req_list[0].lstrip('LOOKUP RFC ').rstrip(' P2P-CI/1.0')) and (rfc_title == req_list[len(req_list)-1].lstrip('Title: ')):
                response_list.append((rfc_number,rfc_title,hostname,peer_port))
        return response_list

    def remove_peer_record(self,data):
        remove_port=data.lstrip("EXIT:")
        peer_ip= self.addr[0].lstrip("'").rstrip("'")

        #peer_ip= self.addr[0]
        hostname=socket.getfqdn(peer_ip)
        remove_hostname= hostname
        for (peer_hostname,peer_port) in peerlist:
            if peer_hostname==remove_hostname and remove_port==peer_port:
                peerlist.remove((peer_hostname,peer_port))

        i=0
        while(i<(len(rfclist))):
            rfcnumber,title,peer_hostname,peer_port = rfclist[i]
            if peer_hostname== remove_hostname and peer_port== remove_port:
                rfclist.remove(rfclist[i])
                i-=1
                if i<0 : i=0
            else :
                i+=1

        self.conn.close()

if __name__=="__main__":
        p2s_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        SERVER_IP = raw_input("please enter your IP:")
        p2s_socket.bind((SERVER_IP,PORT))
        p2s_socket.listen(10)
        while(1) :
            try :
                server = P2S(p2s_socket.accept())
            except :
                print "Error in connecting/sending data to the peer\n"
            server.start()
