from dragonfly import maximise_function, minimise_function
import socket
import struct
import numpy as np
import matplotlib.pyplot as plt
import time
from dragonfly import maximise_function
import re

N = 3 #number of cam images to average

server_address_probecampost = ('192.168.15.24', 65280)
server_address_probecampostnear = ('192.168.15.25', 65264)
hexapod_address = ('192.168.15.16', 65529)

subcriptionstring = b'Wait>>MeanCounts'
SubcriptionCmdLength = len(subcriptionstring)
sizepack = struct.pack('>i', SubcriptionCmdLength)

subcriptionstring2 = b'Wait>>Centroidx,Centroidy'
SubcriptionCmdLength2 = len(subcriptionstring2)
sizepack2 = struct.pack('>i', SubcriptionCmdLength2)

def update_hex_pos(hexy,hexz,wangle,vangle):
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    hexy = np.round(hexy,4)
    hexz = np.round(hexz,4)
    wangle = np.round(wangle,4)
    vangle = np.round(vangle,4)
    
    hexycommand =bytes("setypos>>"+str(hexy),'ascii')
    #print(hexycommand)
    hexzcommand =bytes("setzpos>>"+str(hexz),'ascii')
    wanglecommand =bytes("setwangle>>"+str(wangle),'ascii')
    vanglecommand =bytes("setvangle>>"+str(vangle),'ascii')
    
    udp_client.sendto(hexycommand, hexapod_address)
    ypos_m = get_current_hex_pos('ypos')
    while np.abs(ypos_m-hexy) > 0.01:
        ypos_m = get_current_hex_pos('ypos')
    time.sleep(1)

    udp_client.sendto(hexzcommand, hexapod_address)
    zpos_m = get_current_hex_pos('zpos')
    while np.abs(zpos_m-hexz) > 0.1:
        zpos_m = get_current_hex_pos('zpos')
    time.sleep(1)
    
    udp_client.sendto(wanglecommand, hexapod_address)
    wpos_m = get_current_hex_pos('wangle')
    while np.abs(wpos_m-wangle) > 0.01:
        wpos_m = get_current_hex_pos('wangle')
    time.sleep(1) 
    
    udp_client.sendto(vanglecommand, hexapod_address)
    vpos_m = get_current_hex_pos('vangle')
    while np.abs(vpos_m-vangle) > 0.01:
        vpos_m = get_current_hex_pos('vangle')
    #time.sleep(1)   
    
    return


def get_cam_mean(cam_server_adress): #select camera
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(cam_server_adress)
    client.sendall(sizepack + subcriptionstring)
    
    #initialise loop
    counts = np.zeros(N)
    i = 0
    
    while i < N:
        size = struct.unpack('>i', client.recv(4))[0]  # Extract the msg size from four bytes - mind the encoding
        str_data = client.recv(size)

        data = re.findall(r'\d+', str_data.decode('ascii'))
        counts[i] = np.int(data[2])
        #print('Data size: %s Data value: %s' % (size, str_data.decode('ascii')))
        i = i+1
    client.close()
    
    meancounts_campost = np.mean(counts) 
    
    return meancounts_campost

def get_cam_centroid(cam_server_adress): #select camera
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(cam_server_adress)
    client.sendall(sizepack2 + subcriptionstring2)
    
    #initialise loop
    centroid = np.zeros([N,2])
    i = 0
    
    while i < N:
        size = struct.unpack('>i', client.recv(4))[0]  # Extract the msg size from four bytes - mind the encoding
        str_data = client.recv(size)

        data = re.findall(r'\d+', str_data.decode('ascii'))
        #print(data)
        centroid[i,0] = np.int(data[2])
        centroid[i,1] = np.int(data[4])
        #print('Data size: %s Data value: %s' % (size, str_data.decode('ascii')))
        i = i+1
    client.close()
    
    cenx = np.mean(centroid[:,0]) 
    ceny = np.mean(centroid[:,1]) 
    
    return [cenx,ceny]

def get_current_hex_pos(parameter):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(hexapod_address)

    subcriptionstring = bytes("Wait>>"+parameter,'ascii')
    #print(subcriptionstring)
    SubcriptionCmdLength = len(subcriptionstring)
    sizepack = struct.pack('>i', SubcriptionCmdLength)


    client.sendall(sizepack + subcriptionstring)
    size = struct.unpack('>i', client.recv(4))[0]  # Extract the msg size from four bytes - mind the encoding
    str_data = client.recv(size)
    #print('Data size: %s Data value: %s' % (size, str_data.decode('ascii')))
    position = np.float(re.findall(r'[-+]?\d+\.\d+', str_data.decode('ascii'))[0])
    
    return position

def opt_align(hexp):
    hexy = hexp[0]
    hexz = hexp[1]
    wangle = hexp[2]
    vangle = hexp[3]

    
    #update hexapod pos
    update_hex_pos(hexy,hexz,wangle,vangle)
    
    #get cam property
    meancounts_campost1 = get_cam_mean(server_address_probecampostnear)
    meancounts_campost2 = get_cam_mean(server_address_probecampost)
    
    meancounts_campost = meancounts_campost1+meancounts_campost2
    
    if meancounts_campost>25:
        cenx1,ceny1 = get_cam_centroid(server_address_probecampost)
        cenx2,ceny2 = get_cam_centroid(server_address_probecampostnear)
    
        cen = np.sqrt((np.abs(cenx1-726)+np.abs(ceny1-585))**2)+np.sqrt((np.abs(cenx2-135)+np.abs(ceny2-97))**2)*6
        
    else:
        cen=2000-meancounts_campost*2
    
    print(np.round(cen))
    return cen

domain = [[-2.11-0.2,-2.11+0.2],[2.18-0.2,2.18+0.2],[-0.60-0.15,-0.60+0.15],[-0.25-0.15,-0.25+0.15]]
max_capital = 100
max_val, max_pt, history = minimise_function(opt_align, domain, max_capital,opt_method='bo')

#finsish set to optimum values
print('We are done here:')
print(max_val)
print(max_pt)
opt_align(max_pt)
