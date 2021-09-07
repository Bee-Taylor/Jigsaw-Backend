import socket
import os
import json
import random



def jigsaw_udp(port):
    UDP_IP_ADDRESS = "127.0.0.1"
    UDP_PORT_NO = port
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
    while True:
        data, addr = serverSock.recvfrom(1024)
        data = data.decode("utf-8")
        data_obj = json.loads(data)

def jigsaw_in(port):
    UDP_IP_ADDRESS = "127.0.0.1"
    UDP_PORT_NO = port
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
    while True:
        data, addr = serverSock.recvfrom(1024)
        data = data.decode("utf-8")
        data_obj = json.loads(data)


def jigsaw_out(port):
    UDP_IP_ADDRESS = "127.0.0.1"
    UDP_PORT_NO = port
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
    while True:
        if "gamestates.json" in os.listdir():
            gs_file = open("gamestates.json")
            gs_string = ""
            for line in gs_file:
                gs_string += line
            gs_obj = json.loads(gs_string)
            for player in gs_obj["players"].keys():
                if gs_obj["players"][player]["game_id"] in gs_obj["games"]:
                    msg = json.dumps(gs_obj["games"][gs_obj["players"][player]["game_id"]]["pieces"])
                    msg_enc = msg.encode("utf8")
                    serverSock.sendto(msg_enc, (gs_obj["players"][player]["last_ip_address"], gs_obj["players"][player]["last_port"]))
        data, addr = serverSock.recvfrom(1024)
        data = data.decode("utf-8")
        data_obj = json.loads(data)