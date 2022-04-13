from inspect import getfile
import pyewf
import pytsk3
import re
import os
import sys

class ewf_Img_Info(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(ewf_Img_Info, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self._ewf_handle.close()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def getfileType(filepath):
    if filepath.split(".")[-1] == 'E01': return "E01"
    else : return "raw"

def read_imagefile(imgpath,imgtype):
    if imgtype == "E01":
        filenames = pyewf.glob(imgpath)
        fshandle = pyewf.handle()
        fshandle.open(filenames)
        img_Info = ewf_Img_Info(fshandle)
    else:
        img_Info = pytsk3.Img_Info(imgpath)

    try:#MULTIPARTITION IMAGE
        partitionTable = pytsk3.Volume_Info(img_Info)
        for partition in partitionTable:
            #print(partition.addr, partition.desc, "%s   %s   (%s)" % (partition.start, partition.start * 512, partition.len))
            if b'Basic data partition' in partition.desc:
                fileSystemObject = pytsk3.FS_Info(img_Info, offset = (partition.start * 512))           
    except IOError:#SINGLE PARTITION IMAGE
        fileSystemObject = pytsk3.FS_Info(img_Info, offset = 0)
    
    return fileSystemObject

def readFile(fsobj,filepath):
    f = fsobj.open(filepath)
    offset=0 
    size=f.info.meta.size
    data = b""
    while offset<size: 
        max_size=min(1024*1024,size-offset) 
        buf = f.read_random(0,max_size) 
        if not buf: 
            break 
        data += buf
        offset+=len(buf)

    return data    
    
def readRFile(fsobj):
    filepath = "/$Extend/$Reparse"
    f = fsobj.open(filepath)
    found = 0
    for attr in f:
        print(attr.info.size, attr.info.name)
        if attr.info.name == b"$R":
            found +=1
        if found == 2:
            break
    if not found:
        print("NOT FOUND")
        return -1

    offset=0 
    size=attr.info.size
    data = b""
    #Read ADS Data file
    while offset < size: 
        buf=f.read_random(offset,size,attr.info.type,attr.info.id)
        if not buf: 
            break 
        data += buf
        offset+=len(buf)
    return data
    

if __name__ == "__main__":
    imgpath = r"C:\Users\plainbit\Desktop\TestSetImg100GB.E01"
    fsobj = read_imagefile(imgpath,getfileType(imgpath))
    readFile(fsobj,"/$MFT")
    #readRFile(imgpath,getfileType(imgpath))

