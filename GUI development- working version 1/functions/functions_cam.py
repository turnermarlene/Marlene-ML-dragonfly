import socket
import struct
import numpy as np
import re

def get_cam_mean(cam_server_adress,N): #select camera
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(cam_server_adress)
    subcriptionstring = b'Wait>>MeanCounts'
    SubcriptionCmdLength = len(subcriptionstring)
    sizepack = struct.pack('>i',SubcriptionCmdLength)
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
 
def get_cam_centroid(cam_server_adress,N): #select camera
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(cam_server_adress)
    subcriptionstring = b'Wait>>Centroidx,Centroidy'
    SubcriptionCmdLength = len(subcriptionstring)
    sizepack = struct.pack('>i',SubcriptionCmdLength)
    client.sendall(sizepack + subcriptionstring)

    #initialise loop
    centroid = np.zeros([N,2])
    i = 0

    while i < N:
        size = struct.unpack('>i', client.recv(4))[0]  # Extract the msg size from four bytes - mind the encoding
        str_data = client.recv(size)

        data = re.findall(r'\d+.\d+', str_data.decode('ascii'))
        #print(data)
        #print('Data size: %s Data value: %s' % (size, str_data.decode('ascii')))
        centroid[i,0] = np.float(data[0])
        centroid[i,1] = np.float(data[1])
        
        i = i+1
    client.close()

    cenx = np.round(np.mean(centroid[:,0]),2)
    ceny = np.round(np.mean(centroid[:,1]),2)

    return [cenx,ceny]

def get_cam_exposure(cam_server_adress):
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(cam_server_adress)
    subcriptionstring = b'Wait>>exposure'
    SubcriptionCmdLength = len(subcriptionstring)
    sizepack = struct.pack('>i',SubcriptionCmdLength)
    client.sendall(sizepack + subcriptionstring)

    size = struct.unpack('>i', client.recv(4))[0]  # Extract the msg size from four bytes - mind the encoding
    str_data = client.recv(size)
    #print('Data size: %s Data value: %s' % (size, str_data.decode('ascii')))
    data = re.findall(r'\d+.\d+', str_data.decode('ascii'))
    exposure = float(data[0])
    client.close()

    return exposure
    
def set_cam_exposure(cam_server_adress,exposure):
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    changecamexposure =bytes("setexposure>>"+str(exposure),'ascii')
    udp_client.sendto(changecamexposure, cam_server_adress)
    return