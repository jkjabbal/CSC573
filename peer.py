import sys,random,platform,threading,datetime,time
import os.path
from socket import *

PORT_NUMBER = 7734
BUFFER_SIZE = 1024000
exit_flag = 0

class P2S (threading.Thread):
    def __init__(self,port):
        threading.Thread.__init__(self)
        self.port=port
        self.host=gethostname()

    def run(self):
        self.p2s_socket = socket(AF_INET,SOCK_STREAM)
        SERVER_IP = raw_input("please enter P2P server ip: ")
        self.p2s_socket.connect((SERVER_IP,PORT_NUMBER))
        add_action = int(input("Enter option : \n 1. ADD RFC's automatically \n 2. Manually ADD RFC's later \n"))
        if add_action == 1 :
            self.add_rfc_auto()
        self.get_user_request()

    def add_rfc_auto(self):
        peer_rfc_list=[]
        for file in os.listdir("."):
            if file.startswith("RFC") :
                peer_rfc_list.append(file)
        for f in peer_rfc_list :
            rfc_title=raw_input("Enter Title for RFC "+f.lstrip("RFC").lstrip()+": \n")
            send_message = self.create_p2s_msg("ADD",self.host,self.port,f.lstrip("RFC").lstrip().rstrip('.txt'),rfc_title)
            self.p2s_socket.send(bytes(send_message))
            data = self.p2s_socket.recv(BUFFER_SIZE)
            print data

    def get_user_request(self):
        while(1) :
            user_action = int(input("Enter option : \n 1. ADD \n 2. LOOKUP \n 3. LIST \n 4. DOWNLOAD RFC \n 5. EXIT \n"))
            if user_action==1 :
                self.handle_add()
            elif user_action==2 :
                self.handle_lookup()
            elif user_action==3 :
                self.handle_list()
            elif user_action==4 :
                self.handle_download()
            elif user_action ==5 :
                self.handle_exit()
                break
            else :
                print "Enter correct input\n"

    def handle_add(self):
        RFC_number=int(input("Enter RFC number \n"))
        RFC_title=raw_input("Enter RFC Title \n")
        RFC_file="RFC "+str(RFC_number)+".txt"
        if RFC_file in os.listdir(".") :
            send_message = self.create_p2s_msg("ADD",self.host,self.port,RFC_number,RFC_title)
            self.p2s_socket.send(send_message)
            data = self.p2s_socket.recv(BUFFER_SIZE)
            print data
        else :
            print "RFC not found in current working directory \n"

    def handle_list(self):
        send_message=self.create_p2s_msg("LIST",self.host,self.port)
        self.p2s_socket.send(send_message)
        data=self.p2s_socket.recv(BUFFER_SIZE)
        print data

    def handle_lookup(self):
        RFC_number=int(input("Enter RFC number \n"))
        RFC_title=raw_input("Enter RFC Title \n")
        send_message=self.create_p2s_msg("LOOKUP",self.host,self.port,RFC_number,RFC_title)
        self.p2s_socket.send(send_message)
        data=self.p2s_socket.recv(BUFFER_SIZE)
        print data

    def handle_download(self):
        RFC_number=int(input("Enter RFC number to be downloaded \n"))
        RFC_title=raw_input("Enter RFC Title to be downloaded\n")
        send_message=self.create_p2s_msg("LOOKUP",self.host,self.port,RFC_number,RFC_title)
        self.p2s_socket.send(send_message)
        data=self.p2s_socket.recv(BUFFER_SIZE)
        download_ip,download_port=self.extract_info_for_download(data,RFC_number,RFC_title)
        if(download_ip!="" and download_port!=""):
            os_name=os.name
            os_release=platform.release()
            os_info=os_name+" "+os_release
            send_message=self.create_p2p_msg(RFC_number,os_info,download_ip)
            self.p2p_socket = socket(AF_INET,SOCK_STREAM)
            self.p2p_socket.connect((download_ip,int(download_port)))
            self.p2p_socket.send(send_message)
            response=self.p2p_socket.recv(BUFFER_SIZE)
            print(response)
            response_list=response.split("\r\n")
            RFC_data=response_list[6:]
            RFC_file="RFC "+str(RFC_number)+".txt"
            with open(RFC_file,"w") as fp:
                for line in RFC_data:
                    fp.writelines(line)
            send_message=self.create_p2s_msg("ADD",self.host,self.port,RFC_number,RFC_title)
            self.p2s_socket.send(send_message)
            response=self.p2s_socket.recv(BUFFER_SIZE)
        else:
            print(data+"\r\n")

    def extract_info_for_download(self,data,RFC_number,RFC_title):
        response = data.split("\r\n")
        if("OK" in response[0]):
            download_info=response[1].lstrip("RFC "+str(RFC_number)+" "+RFC_title)
            download_hostname=download_info.split(" ")[0]
            download_port=download_info.split(" ")[1]
            download_ip=gethostbyname(download_hostname)
            return(download_ip,download_port)
        else:
            return("","")

    def create_p2p_msg(self,RFC_number,os_info,download_ip):
        download_host=gethostbyaddr(download_ip)
        msg=""
        msg=msg+"GET "
        msg=msg+"RFC "+str(RFC_number)+" "
        msg=msg+"P2P-CI/1.0"+"\r\n"
        msg=msg+"Host: "+str(download_host)+"\r\n"
        msg=msg+"OS: "+os_info+"\r\n"
        return msg

    def handle_exit(self):
        global exit_flag
        send_message = "EXIT:"+str(self.port)
        self.p2s_socket.send(send_message)
        self.p2s_socket.close()
        exit_flag =1
        return

    def create_p2s_msg(self,method,host,port,RFC_number=0,RFC_title=""):
        msg = ""
        msg = msg+method+" "
        if RFC_number !=0 :
            msg = msg+"RFC "+str(RFC_number)+" "
        msg = msg + "P2P-CI/1.0"+"\r\n"
        msg = msg + "Host: "+host+"\r\n"
        msg = msg + "Port: "+str(port)
        if RFC_title :
            msg = msg+"\r\n"+"Title: "+RFC_title

        return  msg

class P2P(threading.Thread):
    def __init__(self,port):
        threading.Thread.__init__(self)
        self.uploadport=port
        self.hostname=gethostname()
        self.ip=gethostbyname(self.hostname)

    def run(self):
        global  exit_flag
        p2p_socket = socket(AF_INET,SOCK_STREAM)
        p2p_socket.bind((self.ip,self.uploadport))
        p2p_socket.listen(10)
        while not exit_flag :
            try :
                client = P2PClient(p2p_socket.accept())
            except :
                print "Error in connecting/sending data to the peer\n"
            client.start()
        exit()

class P2PClient(threading.Thread):
    def __init__(self,client_info):
        threading.Thread.__init__(self)
        self.conn = client_info[0]
        self.addr = client_info[1]

    def run(self):
        request=self.conn.recv(BUFFER_SIZE)
        self.parse_request(request)

    def parse_request(self,request):
        self.verify_request(request)
        send_message=self.create_p2p_msg()
        self.conn.send(send_message)

    def verify_request(self,request):
        self.status_code=0
        self.status_reason=""
        req_list=request.split('\r\n')
        if "P2P-CI/1.0" not in req_list[0] :
            self.status_code=505
            self.status_reason="P2P-CI Version Not Supported"
        elif not ((req_list[0].startswith("GET")) and (req_list[1].startswith("Host: ") and req_list[2].startswith("OS: "))):
            self.status_code=400
            self.status_reason="Bad Request"
        else :
            self.rfc=req_list[0].lstrip("GET ").rstrip(" P2P-CI/1.0")+".txt"
            for file in os.listdir("."):
                if file == self.rfc:
                    self.status_code=200
                    self.status_reason="OK"
                    break
                else:
                    self.status_code=404
                    self.status_reason="Not Found"

    def create_p2p_msg(self):
        os_name=os.name
        os_release=platform.release()
        os_info=os_name+" "+os_release
        msg = ""
        msg = msg + "P2P-CI/1.0 "+str(self.status_code)+" "+self.status_reason+"\r\n"
        msg = msg + "Date: "+datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")+"\r\n"
        msg = msg + "OS: "+os_info+"\r\n"
        if(self.status_code == 200):
            with open(self.rfc) as fp:
                file_data=fp.read()
                msg = msg + "Last-Modified: "+str(time.ctime(os.path.getmtime(self.rfc))) +"\r\n"
                msg = msg + "Content-Length: " + str(os.stat(self.rfc).st_size) + "\r\n"
                msg = msg + "Content-Type: text/plain"+"\r\n"
                msg = msg + file_data
        return  msg

if __name__=="__main__" :
    port = input("Enter upload port number for the peer: \n")
    peer=P2S(port)
    peer.start()
    peertopeer=P2P(port)
    peertopeer.start()

