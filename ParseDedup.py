from pyfiglet import Figlet
from tqdm import tqdm
import statistics
import argparse
import pytsk3
import pyewf
import time
import sys
import re
import os

import Filesystem as FS
import e01parser as e01

#FILE_PATH = "C:/Users/stars/Desktop/files/"
# FILE_PATH = "C:/Users/plainbit/Desktop/files/"
# MFT_PATH = FILE_PATH+"$MFT"
# RAW_IMAGE_PATH = FILE_PATH+"Final_Testset.001"
# R_FILEPATH = FILE_PATH+"$R"
# DATAFILE_PATH = FILE_PATH+"data/"
# STREAMFILE_PATH = FILE_PATH+"stream/"
# IMGPATH = r"C:\Users\plainbit\Desktop\TestSetImg100GB.E01"

class DedupAssemble:
#     def __init__(self,filepath):
#         self.FSobj = e01.read_imagefile(filepath,e01.getfileType(filepath))

#         self.run1(filepath)
#         # self.run_all(filepath)
#         # self.Recover_datarun(filepath)
#         # self.Recover_stream(filepath)
#     def recover_all(self,filepath):
#         self.Recover_datarun(filepath)
#         self.Recover_stream()
#     def run_all(self,filepath):
#         start = time.time()
#         res =self.run1(filepath)
#         res = self.run2(res)
#         count = 1
#         for i in tqdm(res,desc="Assembling Files"):
#             if self.run3(i) > 0:
#                 count +=1

#         end = time.time()

#         # Statistics
#         self.statistics(len(res),count,end-start)    
        
#     def statistics(self,total,count,time):
#         print("")
#         print("[+]Total Deduplicated File Count : " + str(total))
#         print("[+]Total Reassembled File Count : "+str(count-1))
#         print("[+]Reassemble(Recovery) Rate : "+str(100*(count-1)/total)+"%")
#         print("[+]Elapsed Time : "+ str(time))
#         print("")
    def run1(self,filepath):
        Rdata = e01.readRFile(self.FSobj)
        #Read $R back index
        Record = self.read_R(Rdata)
        
        #Get MFT information
        reparse = []
        MFTdata = e01.readFile(self.FSobj,"/$MFT")
        for rec in Record:
            if rec['Reparse Tag'] != b"\x13\x00\x00\x80":
                print("ERROR")
                continue
            try:
                reparse.append(self.read_MFT_attribute(MFTdata,rec['MFT address']))
            except:
                continue
        
        #Read Run Data
        rundata=[]
        fp = open(RAW_IMAGE_PATH,'rb') # open whole filesystem just for now, will be replaced with libewf
        for i in reparse:
            tmp = self.read_DataRun(fp,i['RUN1'])
            tmp['FileName'] = i['FileName']
            rundata.append(tmp)    
        fp.close()        
            
        return rundata
    def run2(self,rundata):
        #Read Stream File -> Datafile --> Assemble Process
        count = 1        
        outputfile = b""
        #get every stream file
        stream = self.find_StreamFile(rundata)
        #Exceptions
        if type(stream) == int:
            return -1
        stream = sorted(stream,key=lambda d:d['Cumulative Chunk Size'])
        filename = rundata['FileName'].replace(b'\x00\x00',b'').decode('utf16')
        return stream,filename
    def run3(self,stream,filename):
        cumul = 0       
        flag = 0 
        prev_cumul = 0
        #find datafile & Concat
        for j in stream:
            print(j)
            data = self.read_Datafile(j,prev_cumul)
            if type(data) == int:
                flag = 1
                print("ERROR Reading Data File. ERRORCODE :"+str(data))
                break
            cumul += j['Chunk Size']
            outputfile += data
        if flag ==1 : 
            return -1
        
        #Create File
        filename = rundata['FileName'].replace(b'\x00\x00',b'').decode('utf16')
        if filename != "":
            fp = open("./RESULT/"+filename,'wb')
            count +=1
        else:
            fp = open('./RESULT/CARVEDFILE'+str(count),'wb')
            count +=1
        fp.write(outputfile)
        fp.close()
        return 1   
    
#     def Recover_datarun(self,filepath):
#         #find datarun siganture
#         start = time.time()
#         count = 1

#         data = open(RAW_IMAGE_PATH,'rb').read()
#         find_datarun = []
#         while(1):
#             try:
#                 offset = self.search_engine(data,b"\x13\x00\x00\x80\x80\x01\x00\x00")
#                 if offset == -1 :
#                     print("Completed Searching...")
#                     break
#                 size = int.from_bytes(data[offset+0x04:offset+0x08],byteorder='little')
#                 find_datarun.append(FS.parse_Reparse(data[offset:offset+size])) 
#                 data = data[offset:]
#             except:
#                 print("Searching Error...!")
#                 break
#         #get existing datarun offsets
#         cur_datarun = self.run1(filepath)
#         #compare offsets
#         unused_datarun = []
#         for i in find_datarun:
#             for j in cur_datarun:
#                 if i == j:
#                     continue
#             unused_datarun.append(i)
        
#         #get file
#         stream = self.run2(unused_datarun)
#         for i in tqdm(stream,desc='Recovering With Unused DataRuns.'):
#             if self.run3(i) > 0:
#                 count +=1
#         end = time.time()

#         self.statistics(len(cur_datarun),count,end-start)
#     def Recover_stream(self,filename):
#         start = time.time()
#         #Read Delete.log File
#         fp = open(FILE_PATH+'00010000.00000002.delete.log','rb')
#         res_tmp = FS.parse_DeleteLog(fp.read())
        
#         #WhiteListing
#         whitelist =[]
#         for record in res_tmp['Records']:
#             whitelist.append((record['Hash Stream Number'],record['Hash']))

#         print(whitelist)
        
#         #find stream header signature
        
#         data = b""
#         for file in os.listdir(STREAMFILE_PATH):
#             if ".ccc" not in file: continue
#             else: 
#                 data += open(file,'rb').read()
#         find_stream = []
#         while(1):
#             try:
#                 offset = self.search_engine(data,b"\x43\x68\x68\x72\x01\x03\x03\x01")
#                 if offset == -1 :
#                     print("Completed Searching...")
#                     break
#                 size = 0x70
#                 stream_hdr = FS.parse_streamheader(data[offset:offset+size])
#                 num = (stream_hdr['SMAP Size'] - 8) // 0x40
#                 #Read Stream Data
#                 stream_data = []
#                 for i in range(0,num):
#                     stmd = data[offset+size+0x40*i:offset+size+0x40*(i+1)]
#                     stream_data.append(FS.parse_streamdata(stmd))
#                 data = data[offset:]
#             except:
#                 print("Searching Error...!")
#                 break
#         #get existing streams
#         cur_stream,dummy = self.run2(self.run1(filename))
#         #compare
#         unused_stream = []
#         for i in find_stream:
#             for j in cur_stream:
#                 if i == j:
#                     continue
#             print(i,j)
#             unused_stream.append(i)

#         #get file
#         count =1
#         for i in unused_stream:
#             if self.run3(i) > 0:
#                 count +=1
#             for white in whitelist:
#                 if white ==###### 
#         end = time.time()

#         self.statistics(len(find_stream),count,end-start)
    
    def find_StreamFile(self,run):
        flag = 0
        for file in os.listdir(STREAMFILE_PATH):
            if ".ccc" not in file: continue
            else: 
                stream = self.read_Streamfile(file,run)
                flag =1
                break
        if flag ==1 : return stream
        else: return -1
    # def read_R(self,data):
    #     res = FS.parse_R(data)
        
    #     offset = res['Entry Offset']
    #     Record = []
        
    #     for i in range(0,(res['Entry Size'] // 0x20 )):
    #         record_data = data[offset:offset+0x20]
    #         if record_data[0x10:0x14] != b"\x13\x00\x00\x80":
    #             continue
    #         Record.append(FS.parse_Record(record_data))
    #         offset += 0x20
    #     return Record   
    def read_MFT_attribute(self,handle,offset):
        handle.seek(offset)
        data = handle.read(0x400)
        mft = FS.parse_MFT(data)

        res = FS.parse_Reparse(mft['$REPARSE_POINT'])
        filename= self.get_Filename(mft['$FILE_NAME'])
        res['FileName'] = filename

        return res
#     def read_DataRun(self,handle,run):
#         handle.seek(run[1]*0x1000)
#         data = handle.read(CLUSTER_SIZE * run[0])
#         return FS.parse_Dedup(data)
    def read_Streamfile(self,filename,record):
        try:
            fp = open(STREAMFILE_PATH+filename,'rb')
        except:
            return -1
        fp.seek(record['Stream file Offset'])
        data = fp.read(0x70)
        stream_hdr = FS.parse_streamheader(data)
    
        #VALIDATION!!!
        if stream_hdr['Signature'] != b"\x43\x6B\x68\x72\x01\x03\x03\x01": return -1
        if stream_hdr['Stream Hash'] != record['Hash']: return -2
        if stream_hdr['SMAP Size'] != record['SMAP Size'] : return -3
        if stream_hdr['Hash Stream Number'] != record['Hash Stream number1']: return -4

        #Calculate SMAP
        num = (stream_hdr['SMAP Size'] - 8) // 0x40
        #Read Stream Data
        stream_data = []
        for i in range(0,num):
            fp.seek(record['Stream file Offset']+0x70+(0x40 * i))
            stmd = fp.read(0x40)
            stream_data.append(FS.parse_streamdata(stmd))
        
        return stream_data
#     def read_Datafile(self,stream,prev_cumul):
#         fp = open(DATAFILE_PATH+stream['Data File Name'],'rb')
#         fp.seek(stream['Data Offset'])
#         data = fp.read(0x48)
#         chunk_info = FS.parse_Datachunk(data)
        
#         #VALIDATION!!!        
#         if chunk_info['Chunk Number'] != stream['Chunk Number']: return -1
#         if chunk_info['Data Hash'] != stream['Hash']: return -2
#         if chunk_info['Chunk Size'] !=stream['Chunk Size']: return -3
#         #CUMULATIVE CHUNKSIZE CHECK!!
#         fp.seek(stream['Data Offset']+0x58)
#         chunk_data = fp.read(stream['Chunk Size'])
#         fp.close()

#         return chunk_data
    def get_Filename(self,attr):
        namelen = attr[0x50]
        name = attr[0x5A:]
        return name
#     def search_engine(self,data,word):
#         lst = re.search(word,data)
#         if lst == None:
#             return -1
#         else:
#             return lst.start()
    
            
def exit(msg):
    print("\n  [+] "+msg)
    input("\nPress Any Key To Exit.")
    sys.exit()

def start():
    f = Figlet(font='slant')
    print("-------------------------------------------------------------------------------")
    print(f.renderText('DedupExtractor'))
    print("")
    print("Version : 20220519")
    print("Made By : vared.kr")
    print("Conatact : starson1234[at]]gmail[dot]com")
    print("Download : https://github.com/starson1/WinDedup_Extracter_NEW")
    print("-------------------------------------------------------------------------------")

    parser = argparse.ArgumentParser(description="Windows Server Deuplication Extractor/Recovery")
    parser.add_argument('-i','--input',dest='input',type=str,required=True,help="Input File Path (E01 file)")
    parser.add_argument('-o','--outdir',dest='outdir',type=str,required=True,help="Output Directory for Results")
    parser.add_argument('-a','--all',dest='all',action='store_true',help="Extract All Deduplicated Files")
    parser.add_argument('-f','--filename',dest='filename',type=str,nargs="*",help="Extract By Filename (Multi-Input Allowed)")
    parser.add_argument('-c','--carve',dest='carve',action='store_true',help="Carve Searching Unallocated Area (Unsupported)")
    parser.add_argument('-r','--runlist',dest='runlist',action='store_true',help="Recovery Using Runlist Structure (Unallocated Area)")
    parser.add_argument('-s','--stream',dest='stream',action='store_true',help="Recovery Using Stema File (Allocated Area)")

    args = parser.parse_args()

    #check input file
    args.input = os.path.abspath(args.input)
    if os.path.exists(args.input)==False:
        exit("Invalid Input...")
        
    #check output directory
    args.outdir = os.path.abspath(args.outdir)
    if os.path.isdir(args.outdir)==False:
        os.makedirs(args.outdir)

    #check for options
    if (args.all == False) and (args.filename == None) and (args.carve == False) and (args.runlist == False) and (args.stream == False):
        parser.print_help()
        exit("Select More Than 1 Option...")
    if (args.filename != None):
        if len(args.filename) == 0:
            exit("-f option : No Filename given...")


    return args

class Assemble:
    def __init__(self,e01path,odir):
        self.e01path = e01path
        self.outPath = odir
        self.fs = e01.E01_handler(self.e01path)
        
    def assemble_all(self):
        #Read $R file
        r_data = self.fs.readADSFile(self.fs.fsobj,"/$Extend/$Reparse","$R")
        r_meta = FS.parse_R(r_data)
        
        offset = r_meta['Entry Offset']
        r_record = []
        for i in range(0,(r_meta['Entry Size'] // 0x20 )):
            record_data = r_data[offset:offset+0x20]
            if record_data[0x10:0x14] == b"\x13\x00\x00\x80":
                r_record.append(FS.parse_Record(record_data))
            offset += 0x20
        
        print(r_record[0])
        #find&parse file in $MFT entry
        MFThandle = self.fs.fsobj.open('/$MFT')
        entries = []
        for rec in r_record:
            if rec['Reparse Tag'] == b"\x13\x00\x00\x80":
                entries.append(FS.parse_MFT(MFThandle,rec['MFT address']))
        print(entries[0])
        
        #get&parse RunList
        rundatas=[]
        for entry in entries:
            rundata = FS.parse_DataRun(self.fs.raw_handle,entry['RUN1'])
            rundata['FileName'] = entry['FileName']
            rundatas.append(rundata)    
        print(len(rundatas))
        
        #get&parse Stream
        streams_list = {}
        for rundata in rundatas:
            stream_dir = self.fs.fsobj.open_dir(path="/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/")
            count = 0
            for fobj in stream_dir:
                count +=1
                if count == stream_dir.size:
                        print("  [+] File with Error : "+rundata['FileName'])
                if bytes(".ccc",encoding='utf8') not in fobj.info.name.name:
                    continue
                streamfile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/"+fobj.info.name.name.decode('utf8'))
                streams,filename = FS.find_streamfile(streamfile,rundata) 
                if type(streams) == list: 
                    streams_list[filename] = streams
                    break
                
        #get Data
        for name,_streams in streams_list.items():
            cumul = 0       
            flag = 0 
            prev_cumul = 0
            fp = open("\\".join([self.outPath,"AllDedupFiles",name]))
            for _stream in _streams:
                datafile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Data/"+_stream['Data File Name'])
                data = FS.parse_datafile(datafile,_stream)
                if type(data) == int:
                    flag = 1
                    print("ERROR Reading Data File. ERRORCODE :"+str(data))
                    break
                cumul += _stream['Chunk Size']
                outputfile += data
        if flag ==1 : 
            return -1
     
        


        #write
        

    def assemble_file(self,filelist):
        for file in filelist:
            #find&parse file in $MFT entry
            offset,size = e01.E01_handler.get_MFT()
            e01.E01_handler.find_file_in_MFT(offset,size, file)

            #get&parse RunList

            #get&parse Stream

            #get Data

            #write
            fp = open("\\".join([self.outPath,"DedupFiles",file]))


    
class Recover:
    def __init__(self):
        self.e01path=""

if __name__ == "__main__":
    args = start()

    #Assemble - Extract
    if args.all == True:
        #create output dir
        outputDir = "\\".join([args.outdir,'AllDedupFiles'])
        if os.path.exists(outputDir)==False:
            os.mkdir(outputDir)
        
        #parse all
        a = Assemble(args.input,args.outdir)
        a.assemble_all()
        
    if args.filename != None:
        #create output dir
        outputDir = "\\".join([args.outdir,'DedupFiles'])
        if os.path.exists(outputDir)==False:
            os.mkdir(outputDir)
        
        #parse by file
        f = Assemble(args.input,outputDir)
        f.assemble_file(args.filename)

        #write file info
    
    #Recovery
    if args.carve == True:
        print("TBD carve")
    if args.runlist == True:
        print("TBD runlist")
    if args.stream == True:
        print("TBD ")
    
    