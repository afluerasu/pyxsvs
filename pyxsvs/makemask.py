#! /usr/bin/env python2

""" Draw a mask on the existing SAXS file to define ROI for calculations. The
mask is a NxM array of 0 and 1, with 1 indicating the masked pixels, which are
later excluded from analysis.

**Usage:**

   - makemask.py -i </path/to/input.txt> -s </path/to/static.edf>

**Requirements:**

    - Static file (output of createStatic.py) must be present.

**Output:**
    
    - A mask.edf file, saved into the data directory specified in the input file.
        Additionally, the absolute path to the created mask file is added to the 
        Main section of the input file.
"""

from pylab import zeros,figure,show,title,shape,connect,draw,nonzero,close
from ConfigParser import RawConfigParser
from matplotlib.path import Path
import pyxsvs
import sys
import numpy as n
import fabio
import argparse # parsing command line arguments

class maskMaker:
    '''Class defining the mask drawing tool.
    '''
    def __init__(self, data, auto_mask, savedir):
        '''The constructor initializes all the variables and creates the plotting window.

        **Input arguments:**
            
            - *data*: NxM array
                The background to be masked - an averaged (static) scattering image.

            - *auto_mask*: NxM array
                The default mask, masking all the bad pixels.

            - *savedir*: string
                Directory where the mask file will be saved.
        '''
        self.mask_saved = False
        self.savedir = savedir
        self.fig = figure()
        title('Select ROI to mask. Press m to mask or w to save and exit ')
        self.ax = self.fig.add_subplot(111)
        self.canvas = self.ax.figure.canvas
        #self.data = n.log10(data)
        self.data = data
        self.lx, self.ly = shape(self.data)
        self.auto_mask = auto_mask
        self.mask = auto_mask
        self.masked_data = n.ma.masked_array(self.data,self.mask)
        self.points = []
        self.key = []
        self.x = 0
        self.y = 0
        self.xy = []
        self.xx = []
        self.yy = []
        self.ind = 0
        self.img = self.ax.imshow(self.masked_data,origin='lower',interpolation='nearest',animated=True)
        self.lc,=self.ax.plot((0,0),(0,0),'-+w',color='black',linewidth=1.5,markersize=8,markeredgewidth=1.5)
        self.lm,=self.ax.plot((0,0),(0,0),'-+w',color='black',linewidth=1.5,markersize=8,markeredgewidth=1.5)
        self.ax.set_xlim(0,self.lx)
        self.ax.set_ylim(0,self.ly)
        for i in range(self.lx):
            for j in range(self.ly):
                self.points.append([i,j])

        cidb = connect('button_press_event', self.on_click)
        cidk = connect('key_press_event',self.on_click)
        cidm = connect('motion_notify_event',self.on_move)

    def on_click(self,event):
        '''The function handling mouse left-click event. Each clicked pixel
        is added to a list which defines a polygon. After pressing ``m``
        the created polygon is masked. Pressing ``w`` saves the mask
        and closes the plot window.

        **Arguments:**
            - *event*: mouse left-click event

        **Notes**:
            - unmasking is not yet properly implemented
        '''
        if not event.inaxes:
            self.xy = []
            return
        self.x, self.y = int(event.xdata), int(event.ydata)
        self.key = event.key
        self.xx.append([self.x])
        self.yy.append([self.y])
        self.xy.append([self.y,self.x])
        self.lc.set_data(self.xx,self.yy)
        if self.key == 'm':
            self.xx[-1] = self.xx[0]
            self.yy[-1] = self.yy[0]
            self.xy[-1] = self.xy[0]
            self.ind = Path(self.xy).contains_points(self.points)
            self.mask = self.mask.reshape(self.lx*self.ly,1)
            self.mask[self.ind] = 1
            self.mask = self.mask.reshape(self.lx,self.ly)
            self.update_img()
            self.reset_poly()
        draw()
        if self.key == 'u':
            self.xx[-1] = self.xx[0]
            self.yy[-1] = self.yy[0]
            self.xy[-1] = self.xy[0]
            self.ind = Path(self.xy).contains_points(self.points)
            self.mask = self.mask.reshape(self.lx*self.ly,1)
            self.mask[self.ind] = 0
            self.mask = self.mask.reshape(self.lx,self.ly)
            self.update_img()
            self.reset_poly()
        draw()
        if self.key == 'w':
            # Inverting the mask
            #self.mask = (self.mask+1)%2
            edfImg = fabio.edfimage.edfimage()
            edfImg.data = self.mask
            edfImg.write(self.savedir+'mask.edf')
            print 'Mask saved to %s' % (self.savedir+'mask.edf')
            self.mask_saved = True
            close()

    def on_move(self,event):
        '''Function following the movement of mouse cursor in the figure axes
        and plotting a line from the last clicked point to current cursor
        position.
        '''
        if not event.inaxes: return
        self.xm, self.ym = int(event.xdata), int(event.ydata)
        if self.x != 0:
            self.lm.set_data((self.x,self.xm),(self.y,self.ym))
            draw()

    def update_img(self):
        '''Replotting the static image with the current mask
        '''
        self.img.set_data(n.ma.masked_array(self.data,self.mask))
        draw()

    def reset_poly(self):
        '''Resetting the polygon.
        '''
        self.xx = []
        self.yy = []
        self.xy = []
        self.lc.set_data(self.xx,self.yy)
        self.lm.set_data(self.xx,self.yy)
        draw()
        self.x = 0
        self.y = 0



if __name__ == '__main__':
    module_desc = '''A simple GUI tool to create a mask for XSVS data analysis.
                   Requires an input file with information about the data set and 
                   a static file, created with the createStatic.py script.'''
    parser = argparse.ArgumentParser(description=module_desc)
    parser.add_argument('-i','--input',dest='inputFileName', metavar='./input.txt', type=str,
                               help='Input file describing the data',required=True)
    parser.add_argument('-s','--static',dest='staticFileName', metavar='./static.edf', type=str,
                               help='Static file',required=True)
    args = parser.parse_args()

    inputFile = args.inputFileName[0]
    staticFile = args.staticFileName[0]
    calculator = pyxsvs.pyxsvs(inputFile)
    saveDir = calculator.Parameters['saveDir']
    defaultMaskFile = calculator.Parameters['defaultMaskFile']
    auto_mask = fabio.open(defaultMaskFile).data
    staticImg = fabio.open(staticFile).data
    masker = maskMaker(staticImg,auto_mask,saveDir)
    show()
    if masker.mask_saved:
        print 'Adding mask to input file'
        calculator.config.set('Main','mask',value = saveDir+'mask.edf')
        f = open(inputFile,'w')
        calculator.config.write(f)
        f.close()
