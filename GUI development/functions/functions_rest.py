import tkinter as tk
from dragonfly import maximise_function, minimise_function
import socket
import struct
import numpy as np
import time
import re
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

import sys
sys.path.append("functions")
from functions_hexapod import *
from functions_cam import *

class GUI:    
    def __init__(self, master):
        self.fig,self.ax = plt.subplots(figsize=(5,3))
        self.ax.set_xlabel('Step Nr.')
        self.ax.set_ylabel('Quality')
        self.ax.axhline(30,color='tab:red')
        self.fig.tight_layout()
        
        #define global variables
        self.draw_counts = 0

        self.server_address_probecampost = ('192.168.15.24', 65280)
        self.server_address_probecampostnear = ('192.168.15.25', 65264)
        self.hexapod_address = ('192.168.15.16', 65529)

        #define window
        self.master = master
        master.title('ML Capillary Alignment')
        master.geometry("550x550")
        master.option_add( "*font", "Calibri 10" )
        
        self.findsignalupdatemessage= tk.StringVar()
        self.findsignal_display = tk.Label(master, textvariable=self.findsignalupdatemessage, width=70, anchor='w',fg='red')
        self.findsignalupdatemessage.set(' ')
        self.findsignal_display.place(x=20,y=480)
        self.Findsignal = tk.Button(master, text="Find Beam",command=self.search_for_signal ,bg='red')
        self.Findsignal.place(x=20,y=500)
        
        self.prealignmentupdatemessage= tk.StringVar()
        self.message_display_pre = tk.Label(master, textvariable=self.prealignmentupdatemessage, width=70, anchor='w',fg='red')
        self.prealignmentupdatemessage.set(' ')
        self.message_display_pre.place(x=100,y=480)
        self.PreAlign = tk.Button(master, text="Pre-Alignment",command=self.optimise_coarse,bg='red')
        self.PreAlign.place(x=100,y=500)
        
        self.Align = tk.Button(master, text="Alignment",bg='red')
        self.Align.place(x=200,y=500)

        #Camera centroid input
        tk.Label(text='Starting Point', width=15).grid(row=0,column=1)
        tk.Label(text='Range', width=15).grid(row=0,column=2)
        tk.Label(text='Hex y: ', width=15).grid(row=1,column=0)
        tk.Label(text='Hex z: ', width=15).grid(row=2,column=0)
        tk.Label(text='Wangle: ', width=15).grid(row=3,column=0)
        tk.Label(text='Vangle: ', width=15).grid(row=4,column=0)

        hexy_prefill = get_current_hex_pos('ypos',self.hexapod_address)
        hexz_prefill = get_current_hex_pos('zpos',self.hexapod_address)
        hexw_prefill = get_current_hex_pos('wangle',self.hexapod_address)
        hexv_prefill = get_current_hex_pos('vangle',self.hexapod_address)

        self.e_hexy = tk.Entry(master)
        self.e_hexy.insert(0,hexy_prefill)
        self.e_hexy.grid(row=1, column=1)

        self.e_hexz = tk.Entry(master)
        self.e_hexz.insert(0,hexz_prefill)
        self.e_hexz.grid(row=2, column=1)

        self.e_wangle = tk.Entry(master)
        self.e_wangle.insert(0,hexw_prefill)
        self.e_wangle.grid(row=3, column=1)

        self.e_vangle = tk.Entry(master)
        self.e_vangle.insert(0,hexv_prefill)
        self.e_vangle.grid(row=4, column=1)

        self.e_hexy_r = tk.Entry(master)
        self.e_hexy_r.insert(0,0.2)
        self.e_hexy_r.grid(row=1, column=2)

        self.e_hexz_r = tk.Entry(master)
        self.e_hexz_r.insert(0,0.2)
        self.e_hexz_r.grid(row=2, column=2)

        self.e_wangle_r = tk.Entry(master)
        self.e_wangle_r.insert(0,0.15)
        self.e_wangle_r.grid(row=3, column=2)

        self.e_vangle_r = tk.Entry(master)
        self.e_vangle_r.insert(0,0.15)
        self.e_vangle_r.grid(row=4, column=2)

        tk.Label(text='N. Cam: ', width=15).grid(row=5,column=0)
        self.Ncamimg = tk.Entry(master)
        self.Ncamimg.insert(0,5)
        self.Ncamimg.grid(row=5, column=1)
        self.N = np.int(self.Ncamimg.get())

        tk.Label(text='Capital: ', width=15).grid(row=6,column=0)
        self.Capital = tk.Entry(master)
        self.Capital.insert(0,50)
        self.Capital.grid(row=6, column=1)

        tk.Label(text='Centroid x', width=15).grid(row=7,column=1)
        tk.Label(text='Centroid y', width=15).grid(row=7,column=2)

        tk.Label(text='Cam 1: ', width=15).grid(row=8,column=0)
        self.e_cen1x = tk.Entry(master)
        self.e_cen1x.insert(0,135.0)
        self.e_cen1x.grid(row=8, column=1)

        self.e_cen1y = tk.Entry(master)
        self.e_cen1y.insert(0,96.0)
        self.e_cen1y.grid(row=8, column=2)

        tk.Label(text='Cam 2: ', width=15).grid(row=9,column=0)
        self.e_cen2x = tk.Entry(master)
        self.e_cen2x.insert(0,716.7)
        self.e_cen2x.grid(row=9, column=1)

        self.e_cen2y = tk.Entry(master)
        self.e_cen2y.insert(0,586.7)
        self.e_cen2y.grid(row=9, column=2)

        self.centroidupdatemessage= tk.StringVar()
        self.message_display_cen = tk.Label(master, textvariable=self.centroidupdatemessage, width=70, anchor='w',fg='red')
        self.centroidupdatemessage.set(' ')
        self.message_display_cen.place(x=420,y=155)
        self.Initialise = tk.Button(master, text="Get Centroids",command=self.initialise_threading, bg='red')
        self.Initialise.place(x=420,y=175)
        
        tk.Label(text='Algorithm: ', width=15).grid(row=10,column=0)
        optimizeroptions = ['bo','rand','pdoo']
        self.optimizer_var = tk.StringVar()
        self.optimizer_var.set(optimizeroptions[0]) 
        self.drop_method = tk.OptionMenu(master, self.optimizer_var, *optimizeroptions).grid(row=10, column=1)

        #canvas
        tk.Label(text='Optimisation', width=15).grid(row=11,column=0,columnspan=2)
        self.myCanvas = FigureCanvasTkAgg(self.fig,master)
        self.myCanvas.draw()
        self.myCanvas.get_tk_widget().grid(row=12, column=1,columnspan=10)


        #Close GUI Button
        self.button_close = tk.Button(master, text="Close", command=master.destroy,bg='pink')
        self.button_close.place(x=420,y=500)

        self.var= tk.StringVar()
        self.message_display = tk.Label(master, textvariable=self.var, width=110, anchor='w')
        self.var.set('Messages:')
        self.message_display.place(x=0,y=530)
        
    def initialise(self):
        self.var.set('Messages: Getting centroids')
        self.centroidupdatemessage.set('In Progress')
        self.master.update()

        hexy_temp = get_current_hex_pos('ypos',self.hexapod_address)
        hexz_temp = get_current_hex_pos('zpos',self.hexapod_address)
        hexw_temp = get_current_hex_pos('wangle',self.hexapod_address)
        hexv_temp = get_current_hex_pos('vangle',self.hexapod_address)

        update_hex_pos(20.0,float(self.e_hexz.get()),float(self.e_wangle.get()),float(self.e_vangle.get()),self.hexapod_address)

        cenx1,ceny1 = get_cam_centroid(self.server_address_probecampostnear,self.N)
        cenx2,ceny2 = get_cam_centroid(self.server_address_probecampost,self.N)    
        
        self.e_cen1x.delete(0,10)
        self.e_cen1y.delete(0,10)
        self.e_cen2x.delete(0,10)
        self.e_cen2y.delete(0,10)

        self.e_cen1x.insert(0,np.round(cenx1,1))
        self.e_cen1y.insert(0,np.round(ceny1,1))
        self.e_cen2x.insert(0,np.round(cenx2,1))
        self.e_cen2y.insert(0,np.round(ceny2,1))

        update_hex_pos(float(self.e_hexy.get()),float(self.e_hexz.get()),float(self.e_wangle.get()),
                              float(self.e_vangle.get()),self.hexapod_address)

        self.var.set('Messages: Done with centroids')
        self.centroidupdatemessage.set(' ')
        self.Initialise.configure(bg='green')
        self.master.update()
        
        return
    

    def opt_align(self,hexp):
        hexy = hexp[0]
        hexz = hexp[1]
        wangle = hexp[2]
        vangle = hexp[3]

        #update hexapod pos
        update_hex_pos(hexy,hexz,wangle,vangle,self.hexapod_address)

        #get cam property
        meancounts_campost1 = get_cam_mean(self.server_address_probecampostnear,self.N)
        meancounts_campost2 = get_cam_mean(self.server_address_probecampost,self.N)

        meancounts_campost = meancounts_campost1+meancounts_campost2

        if meancounts_campost>10:
            cenx1,ceny1 = get_cam_centroid(self.server_address_probecampostnear,self.N)
            cenx2,ceny2 = get_cam_centroid(self.server_address_probecampost,self.N)

            #get centroids when cap is out from gui
            capout_cenx1 = float(self.e_cen1x.get())
            capout_ceny1 = float(self.e_cen1y.get())
            capout_cenx2 = float(self.e_cen2x.get())
            capout_ceny2 = float(self.e_cen2y.get())

            cen = 8*np.sqrt((np.abs(cenx1-capout_cenx1)+np.abs(ceny1-capout_ceny1))**2)+np.sqrt((np.abs(cenx2-capout_cenx2)+np.abs(ceny2-capout_ceny2))**2)
        else:
            cen=2000-meancounts_campost*2


        self.ax.scatter(self.draw_counts,np.round(cen),color='tab:blue',s=10)
        self.myCanvas.draw()
        self.master.update()
        
        self.draw_counts = self.draw_counts+1

        #print(np.round(cen))

        return cen

    def optimise_coarse(self):
        
        self.draw_counts = 0
        self.plot_canvas()
        self.ax.set_ylim(1,3000)
        self.ax.axhline(30,color='tab:red')
        self.ax.set_yscale('log')
        self.myCanvas.draw()
    
        #get measurement range from gui
        self.var.set('Messages: optimising')
        self.prealignmentupdatemessage.set('In progress')
        self.master.update()
    
        r_hexy = float(self.e_hexy.get())
        r_hexy_r = float(self.e_hexy_r.get())
        r_hexz = float(self.e_hexz.get())
        r_hexz_r = float(self.e_hexz_r.get())
        r_hexw = float(self.e_wangle.get())
        r_hexw_r = float(self.e_wangle_r.get())
        r_hexv = float(self.e_vangle.get())
        r_hexv_r = float(self.e_vangle_r.get())
                     
        domain = [[r_hexy-r_hexy_r,r_hexy+r_hexy_r],[r_hexz-r_hexz_r,r_hexz+r_hexz_r],[r_hexw-r_hexw_r,r_hexw+r_hexw_r],[r_hexv-r_hexv_r,r_hexv+r_hexv_r]]
        max_capital = self.Capital.get()
    
        max_val, max_pt, history = minimise_function(self.opt_align, domain, max_capital,opt_method=self.optimizer_var.get())
        #finsish set to optimum values
        print('We are done here:')
        print(max_val)
        print(max_pt)
        
        final_cen = self.opt_align(max_pt)
        
        self.e_hexy.delete(0,10)
        self.e_hexz.delete(0,10)
        self.e_wangle.delete(0,10)
        self.e_vangle.delete(0,10)
        
        self.e_hexy.insert(0,np.round(max_pt[0],4))
        self.e_hexz.insert(0,np.round(max_pt[1],4))
        self.e_wangle.insert(0,np.round(max_pt[2],4))
        self.e_vangle.insert(0,np.round(max_pt[3],4))
        
        self.prealignmentupdatemessage.set(' ')
        self.var.set('Messages: optimisation is done')
        self.PreAlign.configure(bg='green')
        self.ax.axhline(np.round(final_cen),color='tab:green')
        self.myCanvas.draw()
        self.master.update()
        return
    
    def initialise_threading(self):
        t =  threading.Thread(target=self.initialise) # Create thread
        t.start() # Start thread
        return
    
    def plot_canvas(self):
        self.ax.clear()
        self.ax.set_xlabel('Step Nr.')
        self.ax.set_ylabel('Quality')
        self.fig.tight_layout()
        
        self.myCanvas.draw()
        self.master.update()
        return
    
    def find_counts(self,hexp):
        hexy = hexp[0]
        hexz = hexp[1]
        wangle = hexp[2]
        vangle = hexp[3]

        #update hexapod pos
        update_hex_pos(hexy,hexz,wangle,vangle,self.hexapod_address)

        #get cam property
        meancounts_campost1 = self.get_cam_mean(self.server_address_probecampostnear,self.N)
        meancounts_campost2 = self.get_cam_mean(self.server_address_probecampost,self.N)

        ampl = (meancounts_campost1) + (meancounts_campost2)

        self.ax.scatter(self.draw_counts,np.round(ampl),color='tab:blue',s=10)
        self.myCanvas.draw()
        self.master.update()
        
        self.draw_counts = self.draw_counts+1
        
        if ampl > 1000:
            set_cam_exposure(self.server_address_probecampostnear,0.03)
            set_cam_exposure(self.server_address_probecampost,0.025)

        print(ampl)

        return ampl

    def search_for_signal(self):
        self.draw_counts = 0
        self.plot_canvas()
    
        #get measurement range from gui
        self.var.set('Messages: optimising')
        self.findsignalupdatemessage.set('In progress')
        self.master.update()
    
        r_hexy = float(self.e_hexy.get())
        r_hexy_r = float(self.e_hexy_r.get())
        r_hexz = float(self.e_hexz.get())
        r_hexz_r = float(self.e_hexz_r.get())
        r_hexw = float(self.e_wangle.get())
        r_hexw_r = float(self.e_wangle_r.get())
        r_hexv = float(self.e_vangle.get())
        r_hexv_r = float(self.e_vangle_r.get())
        
        cam1exp = get_cam_exposure(self.server_address_probecampostnear)
        cam2exp = get_cam_exposure(self.server_address_probecampost)
        
        set_cam_exposure(self.server_address_probecampostnear,1.0)
        set_cam_exposure(self.server_address_probecampost,1.0)
                     
        domain = [[r_hexy-r_hexy_r,r_hexy+r_hexy_r],[r_hexz-r_hexz_r,r_hexz+r_hexz_r],[r_hexw-r_hexw_r,r_hexw+r_hexw_r],[r_hexv-r_hexv_r,r_hexv+r_hexv_r]]
        max_capital = self.Capital.get()
    
        max_val, max_pt, history = maximise_function(self.find_counts, domain, max_capital,opt_method=self.optimizer_var.get())
        
        #finsish set to optimum values
        print('We are done here:')
        print(max_val)
        print(max_pt)
        
        set_cam_exposure(self.server_address_probecampostnear,cam1exp)
        set_cam_exposure(self.server_address_probecampost,cam2exp)
        
        final_max = self.find_counts(max_pt)
        
        self.e_hexy.delete(0,10)
        self.e_hexz.delete(0,10)
        self.e_wangle.delete(0,10)
        self.e_vangle.delete(0,10)
        
        self.e_hexy.insert(0,np.round(max_pt[0],4))
        self.e_hexz.insert(0,np.round(max_pt[1],4))
        self.e_wangle.insert(0,np.round(max_pt[2],4))
        self.e_vangle.insert(0,np.round(max_pt[3],4))
        
        self.findsignalupdatemessage.set(' ')
        self.var.set('Messages: signal finding finished')
        self.Findsignal.configure(bg='green')
        self.ax.axhline(np.round(final_max),color='tab:green')
        self.myCanvas.draw()
        self.master.update()
        return
    

