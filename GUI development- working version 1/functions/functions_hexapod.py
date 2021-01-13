import socket
import struct
import numpy as np
import time
import re
import threading

def update_hex_pos(hexy,hexz,wangle,vangle,hexapod_address):
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    hexy = np.round(hexy,3)
    hexz = np.round(hexz,3)
    wangle = np.round(wangle,3)
    vangle = np.round(vangle,3)

    hexycommand =bytes("setypos>>"+str(hexy),'ascii')
    #print(hexycommand)
    hexzcommand =bytes("setzpos>>"+str(hexz),'ascii')
    wanglecommand =bytes("setwangle>>"+str(wangle),'ascii')
    vanglecommand =bytes("setvangle>>"+str(vangle),'ascii')

    udp_client.sendto(hexycommand, hexapod_address)
    ypos_m = get_current_hex_pos('ypos',hexapod_address)
    while np.abs(ypos_m-hexy) > 0.01:
        ypos_m = get_current_hex_pos('ypos',hexapod_address)
    time.sleep(1)

    udp_client.sendto(hexzcommand, hexapod_address)
    zpos_m = get_current_hex_pos('zpos',hexapod_address)
    while np.abs(zpos_m-hexz) > 0.1:
        zpos_m = get_current_hex_pos('zpos',hexapod_address)
    time.sleep(1)

    udp_client.sendto(wanglecommand,hexapod_address)
    wpos_m = get_current_hex_pos('wangle',hexapod_address)
    while np.abs(wpos_m-wangle) > 0.01:
        wpos_m = get_current_hex_pos('wangle',hexapod_address)
    time.sleep(1) 

    udp_client.sendto(vanglecommand, hexapod_address)
    vpos_m = get_current_hex_pos('vangle',hexapod_address)
    while np.abs(vpos_m-vangle) > 0.01:
        vpos_m = get_current_hex_pos('vangle',hexapod_address) 

    return

def get_current_hex_pos(parameter,hexapod_address):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(hexapod_address)

    subcriptionstring = bytes("Wait>>"+parameter,'ascii')
    SubcriptionCmdLength = len(subcriptionstring)
    sizepack = struct.pack('>i', SubcriptionCmdLength)

    client.sendall(sizepack + subcriptionstring)
    size = struct.unpack('>i', client.recv(4))[0]  # Extract the msg size from four bytes - mind the encoding
    str_data = client.recv(size)
    #print('Data size: %s Data value: %s' % (size, str_data.decode('ascii')))
    position = np.float(re.findall(r'[-+]?\d+\.\d+', str_data.decode('ascii'))[0])
    client.close()

    return position