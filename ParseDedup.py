import chunk
from tqdm import trange
from tqdm import tqdm
import struct
import os

import Dedup_Structure as DS

MFT_RECORD_SIZE = 0x400
RAW_IMAGE_PATH = r"E:\#My_Work\WinServer2019\dumps\Dump_1101_OtherFile Added.001"
CLUSTER_SIZE= 0x200

class DedupAssemble:
    def __init__(self,filepath):
        self.filepath = filepath
        self.filename = "" ####GET FILENAME!!
        self.run()

    def run(self):
        #Read $R back index
        fp = open(self.filepath,'rb')
        self.Record = self.read_R(fp)
        fp.close()

        #Get MFT information
        reparse = []
        fp = open("E:\#My_Work\WinServer2019\code\WinDedup_Extracter\File\$MFT",'rb')
        for rec in self.Record:
            if rec['Reparse Tag'] != b"\x13\x00\x00\x80":
                print("ERROR")
            reparse.append(self.read_MFT_attribute(fp,rec['MFT address']))
        fp.close()
        
        #Read Run Data
        rundata=[]
        fp = open(RAW_IMAGE_PATH,'rb') # open whole filesystem just for now, will be replaced with libewf
        for i in reparse:
            rundata.append(self.read_DataRun(fp,i['RUN1']))
        fp.close()

        #Read Stream File & Datafile --> Assemble Process
        for i in rundata:
            outputfile = b""
            stream = self.read_Streamfile(i)
            count =1
            for j in stream:
                data = self.read_Datafile(j)
                outputfile += data
                #CUMULATIVE CHUNKSIZE CHECK!!
            if self.filename != "":
                fp = open('.'+self.filename,'wb')
            else:
                fp = open('.CARVEDFILE'+str(count),'wb')
                count +=1
            fp.write(outputfile)
            fp.close()
            break
            

    def read_R(self,handle):
        data = handle.read()
        res = DS.parse_R(data)
        
        offset = res['Entry Offset']
        Record = []
        
        for i in range(0,(res['Entry Size'] // 0x20 )):
            record_data = data[offset:offset+0x20]
            Record.append({"Reparse Tag" : record_data[0x10:0x14],"Seq Num":record_data[0x1A:0x1C],"MFT Key Reference": record_data[0x14:0x1A],"MFT address":self.Find_MFT_Record(record_data[0x14:0x18])})            
            offset += 0x20
        return Record

    def Find_MFT_Record(self, key_ref:bytes):
        return int.from_bytes(key_ref,byteorder='little') * MFT_RECORD_SIZE
    
    def read_MFT_attribute(self,handle,offset):
        handle.seek(offset)
        data = handle.read(0x400)
        mft = DS.parse_MFT(data)


        return DS.parse_Reparse(mft['$REPARSE_POINT'])

    def read_DataRun(self,handle,run):
        handle.seek(run[1]*0x1000)
        data = handle.read(CLUSTER_SIZE * run[0])
        return DS.parse_Dedup(data)
    def read_Streamfile(self,record):
        fp = open("File/"+record['Stream file name1'],'rb')
        fp.seek(record['Stream file Offset'])
        data = fp.read(0x70)
        stream_hdr = DS.parse_streamheader(data)
        #VALIDATION!!!

        #Calculate SMAP
        num = (stream_hdr['SMAP size'] - 8) // 0x40
        #Read Stream Data
        stream_data = []
        for i in range(0,num):
            fp.seek(record['Stream file Offset']+0x70+(0x40 * i))
            stmd = fp.read(0x40)
            stream_data.append(DS.parse_streamdata(stmd))
        
        #Sort stream_data by Chunk Num
        ## 할까 말까...
        
        return stream_data
    def read_Datafile(self,stream):
        fp = open("File/"+stream['Data File Name'],'rb')
        fp.seek(stream['Data Offset'])
        data = fp.read(0x58)
        chunk_info = DS.parse_Datachunk(data)
        #VALIDATION!!!        
        
        fp.seek(stream['Data Offset']+0x68)
        chunk_data = fp.read(chunk_info['Chunk Size'])
        
        fp.close()
        return chunk_data

        

        

if __name__ == "__main__":
    a = DedupAssemble('E:\#My_Work\WinServer2019\code\WinDedup_Extracter\File\$R') 