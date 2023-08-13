from pyfiglet import Figlet #install
import argparse #install
import pytsk3 #install
import pyewf #install
import time
import sys
import os

import Filesystem as FS
import e01parser as e01

    
def exit(msg):
    for m in msg:
        print("\n  [+] "+m)
    input("\nPress Any Key To Exit.")
    sys.exit()

def dedup_statistic(success,all,t):
    print("")
    print(f"  [+] Detected Files : %d"%all)
    print(f"  [+] Extracted Files : %d"%success)
    if all == 0: print(f"  [+] Extraction Rate(%%) : --%"%(100*success/all))
    else: print(f"  [+] Extraction Rate(%%) : %.2f%%"%(100*success/all))
    print(f"  [+] Elapsed Time : %.2fs"%(t))
    print("")

def start():
    f = Figlet(font='slant')
    print("-------------------------------------------------------------------------------")
    print(f.renderText('DedupExtractor'))
    print("")
    print("Version : 20220817")
    print("Made By : vared.kr")
    print("Contact : starson1234[at]]gmail[dot]com")
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
        exit(["Invalid Input..."])
        
    #check output directory
    args.outdir = os.path.abspath(args.outdir)
    if os.path.isdir(args.outdir)==False:
        try:
            os.makedirs(args.outdir)
        except:
            exit(["Invalid Output Path..."])

    #check for options
    if (args.all == False) and (args.filename == None) and (args.carve == False) and (args.runlist == False) and (args.stream == False):
        parser.print_help()
        exit(["Select More Than 1 Option..."])
    if (args.filename != None):
        if len(args.filename) == 0:
            exit(["-f option : No Filename given..."])


    return args


class Assemble:
    def __init__(self,e01path,odir):
        self.e01path = e01path
        self.outPath = odir
        self.fs = e01.E01_handler(self.e01path)
        self.total =0
        self.start = 0.0
        self.end = 0.0
        
    def assemble_all(self):
        self.start = time.time()
        
        #Read $R file
        print("  [+] Reading $R index file.")
        r_data = self.fs.readADSFile(self.fs.fsobj,"/$Extend/$Reparse","$R")
        r_meta = FS.parse_R(r_data)
        
        offset = r_meta['Entry Offset']
        r_record = []
        for i in range(0,(r_meta['Entry Size'] // 0x20 )):
            record_data = r_data[offset:offset+0x20]
            if record_data[0x10:0x14] == b"\x13\x00\x00\x80":
                r_record.append(FS.parse_Record(record_data))
            offset += 0x20
        self.total =len(r_record)

        #find&parse file in $MFT entry
        print("  [+] Parsing $MFT with $Reparse_Point.")
        MFThandle = self.fs.fsobj.open('/$MFT')
        entries = []
        for rec in r_record:
            if rec['Reparse Tag'] == b"\x13\x00\x00\x80":
                entries.append(FS.parse_MFT(MFThandle,rec['MFT address']))
        
        
        #get&parse RunList
        print("  [+] Parsing MFT Data Run List.")
        rundatas=[]
        for entry in entries:
            rundata = FS.parse_DataRun(self.fs.raw_handle,entry['RUN1'])
            rundata['FileName'] = entry['FileName']
            rundatas.append(rundata)    
        
        
        #get&parse Stream
        print("  [+] Parsing Stream File.")
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
        print("  [+] Reassembling Data Files.")
        count =0
        for name,_streams in streams_list.items():
            cumul = 0      
            comp_count = 0     
            fp = open("\\".join([self.outPath,name.replace(chr(0),"")]),'wb')
            for _stream in _streams:
                datafile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Data/"+_stream['Data File Name'])
                data,comp = FS.parse_datafile(datafile,_stream)
                comp_count += comp
                if type(data) == int:
                    flag = 1
                    print("ERROR Reading Data File. ERRORCODE :"+str(data))
                    break

                #Cumulative ChunkSize Check!
                cumul += len(data)
                if comp_count == 0:
                    if cumul != _stream['Cumulative Chunk Size']:
                        print("     [-] Warning : INVALID Cumulative Chunk Size")
                        print("     [-] Filename : "+name)
                        fp.close()
                        os.remove("\\".join([self.outPath,name.replace("\x00","")]))
                        break
                fp.write(data)
            count +=1
            fp.close()
            print(f"     [-] Warning : Sparse Data Included. {comp_count}/{len(_streams)}")
            print("     [-] Filename : "+name)
            print("")
        
            #write file metadata
        self.end = time.time()
        return count

    def assemble_file(self,file):
        self.start = time.time()
        #find&parse file in $MFT entry
        MFThandle = self.fs.fsobj.open('/$MFT')
        print("  [+] Searching File...")
        i = 0
        while(True):
            print("     ("+"-"*((int(time.time()*5))%20)+"*"+"-"*(20-(int(time.time()*5)%20))+")",end="\r")
            try:
                r_record = FS.parse_MFTattr(MFThandle.read_random(i*0x400,0x400))
            except:
                i +=1
                continue
            if r_record == None:
                i += 1
                continue
            if "$FILE_NAME" in r_record.keys():
                try:
                    filename = str(r_record['$FILE_NAME'][0x5A:].decode('utf8').replace(chr(0),""))
                except:
                    filename = str(r_record['$FILE_NAME'][0x5A:].decode('utf16').replace(chr(0),""))
                if filename == file:
                    r_record['FileName'] = filename
                    break
            i += 1
        if "$REPARSE_POINT" not in r_record.keys():
            self.end = time.time()
            return -1

        #get&parse RunList
        print("  [+] Parsing MFT & Run List.")
        entry = FS.parse_Reparse(r_record['$REPARSE_POINT'])
        entry['FileName'] = r_record["FileName"]
        rundata = FS.parse_DataRun(self.fs.raw_handle,entry['RUN1'])
        rundata['FileName'] = entry['FileName']
        
        #get&parse Stream
        print("  [+] Finding Stream File")
        streams_list = {}
        stream_dir = self.fs.fsobj.open_dir(path="/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/")
        count = 0
        for fobj in stream_dir:
            count +=1
            if count == stream_dir.size:
                    print("     [-] File with Error : "+rundata['FileName'])
            if bytes(".ccc",encoding='utf8') not in fobj.info.name.name:
                continue
            streamfile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/"+fobj.info.name.name.decode('utf8'))
            streams,filename = FS.find_streamfile(streamfile,rundata) 
            if type(streams) == list: 
                streams_list[filename] = streams
                break
        
        #get Data
        print("  [+] Reassembling Data.")
        for name,_streams in streams_list.items():
            cumul = 0
            comp_count = 0    
            fp = open("\\".join([self.outPath,name]),'wb')
            for _stream in _streams:
                print("     ("+"-"*((int(time.time()*5))%20)+"*"+"-"*(20-(int(time.time()*5)%20))+")",end="\r")
                datafile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Data/"+_stream['Data File Name'])
                data,comp = FS.parse_datafile(datafile,_stream)
                comp_count += comp
                if type(data) == int:
                    
                    print("     [-] ERROR Reading Data File. ERRORCODE :"+str(data))
                    break
                
                #Cumulative ChunkSize Check!
                cumul += len(data)
                if comp != 0:
                    if cumul != _stream['Cumulative Chunk Size']:
                        print("     [-] Warning : INVALID Cumulative Chunk Size")
                        print("     [-] Filename : "+name)
                        # fp.close()
                        # os.remove("\\".join([self.outPath,name]))
                        # break
                fp.write(data)
            fp.close()
            print(f"     [-] Warning : Sparse Data Included. {comp_count}/{len(_streams)}")
        
        self.end = time.time()
        return 1
class Recover:
    def __init__(self,e01path,odir):
        self.e01path= e01path
        self.outPath = odir
        self.fs = e01.E01_handler(self.e01path)
        self.total =0
        self.start = 0.0
        self.end = 0.0
    def carve_DataRun(self):
        self.start = time.time()
        MFThandle = self.fs.fsobj.open('/$MFT')
        print("  [+] Searching File...")
        
        deleted_entry = []
        i = 0
        while(i*0x400 < MFThandle.info.meta.size):
            print("     ("+"-"*((int(time.time()*5))%20)+"*"+"-"*(20-(int(time.time()*5)%20))+")",end="\r")
            try:
                r_record = FS.parse_MFTattr(MFThandle.read_random(i*0x400,0x400))
                if r_record == None:
                    i+=1
                    continue
            except:
                i +=1
                continue
            if "$REPARSE_POINT" in r_record.keys():
                if r_record['Flags'] == 0:
                    if r_record == None:
                        i += 1
                        continue
                    if "$FILE_NAME" in r_record.keys():
                        try:
                            filename = str(r_record['$FILE_NAME'][0x5A:].decode('utf8').replace(chr(0),""))
                        except:
                            filename = str(r_record['$FILE_NAME'][0x5A:].decode('utf16').replace(chr(0),""))
                        deleted_entry.append(r_record)
            i += 1
        for r_record in deleted_entry:
            #get&parse RunList
            print("  [+] Parsing MFT & Run List.")
            entry = FS.parse_Reparse(r_record['$REPARSE_POINT'])
            entry['FileName'] = r_record["FileName"]
            rundata = FS.parse_DataRun(self.fs.raw_handle,entry['RUN1'])
            rundata['FileName'] = entry['FileName']

            #get&parse Stream
            print("  [+] Finding Stream File")
            streams_list = {}
            stream_dir = self.fs.fsobj.open_dir(path="/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/")
            count = 0
            for fobj in stream_dir:
                count +=1
                if count == stream_dir.size:
                        print("     [-] File with Error : "+rundata['FileName'])
                if bytes(".ccc",encoding='utf8') not in fobj.info.name.name:
                    continue
                streamfile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/"+fobj.info.name.name.decode('utf8'))
                streams,filename = FS.find_streamfile(streamfile,rundata) 
                if type(streams) == list: 
                    streams_list[filename] = streams
                    break
                
            #get Data
            print("  [+] Reassembling Data.")
            for name,_streams in streams_list.items():
                cumul = 0    
                fp = open("\\".join([self.outPath,name]),'wb')
                for _stream in _streams:
                    print("     ("+"-"*((int(time.time()*5))%20)+"*"+"-"*(20-(int(time.time()*5)%20))+")",end="\r")
                    datafile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Data/"+_stream['Data File Name'])
                    data = FS.parse_datafile(datafile,_stream)
                    if type(data) == int:
                        flag = 1
                        print("     [-] ERROR Reading Data File. ERRORCODE :"+str(data))
                        break
                    
                    #Cumulative ChunkSize Check!
                    cumul += len(data)
                    if cumul != _stream['Cumulative Chunk Size']:
                        print("     [-] Warning : INVALID Cumulative Chunk Size")
                        print("     [-] Filename : "+name)
                        fp.close()
                        os.remove("\\".join([self.outPath,name]))
                        break
                    fp.write(data)
                fp.close()
        self.end = time.time()
    def carve_Stream(self):
        #Get Existing Streams 
        #Read $R file
        self.start = time.time()
        print("  [+] Reading $R index file.")
        r_data = self.fs.readADSFile(self.fs.fsobj,"/$Extend/$Reparse","$R")
        r_meta = FS.parse_R(r_data)
        
        offset = r_meta['Entry Offset']
        r_record = []
        for i in range(0,(r_meta['Entry Size'] // 0x20 )):
            record_data = r_data[offset:offset+0x20]
            if record_data[0x10:0x14] == b"\x13\x00\x00\x80":
                r_record.append(FS.parse_Record(record_data))
            offset += 0x20
        self.total =len(r_record)

        #find&parse file in $MFT entry
        print("  [+] Parsing $MFT with $Reparse_Point.")
        MFThandle = self.fs.fsobj.open('/$MFT')
        entries = []
        for rec in r_record:
            if rec['Reparse Tag'] == b"\x13\x00\x00\x80":
                entries.append(FS.parse_MFT(MFThandle,rec['MFT address']))
        
        #get&parse RunList
        print("  [+] Parsing MFT Data Run List.")
        rundatas=[]
        for entry in entries:
            rundata = FS.parse_DataRun(self.fs.raw_handle,entry['RUN1'])
            rundata['FileName'] = entry['FileName']
            rundatas.append(rundata) 
        
        #get&parse Stream
        print("  [+] Parsing Stream File.")
        streams_inuse = {}
        for rundata in rundatas:
            stream_dir = self.fs.fsobj.open_dir(path="/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/")
            count = 0
            for fobj in stream_dir:
                count +=1
                if count == stream_dir.size+1:
                        print("  [+] File with Error : "+rundata['FileName'])
                        print("      [-] No Stream File Detected.")
                if bytes(".ccc",encoding='utf8') not in fobj.info.name.name:
                    continue
                streamfile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Stream/"+fobj.info.name.name.decode('utf8'))
                streams,filename = FS.find_streamfile(streamfile,rundata) 
                if type(streams) == list: 
                    streamfilename = fobj.info.name.name.decode('utf8')                 
                    if rundata['Chunkstore UID'] not in streams_inuse.keys():
                        streams_inuse[rundata['Chunkstore UID']] = {}
                    if streamfilename not in streams_inuse[rundata['Chunkstore UID']].keys():
                        streams_inuse[rundata['Chunkstore UID']][streamfilename]=[]
                    streams_inuse[rundata['Chunkstore UID']][streamfilename].append(rundata['Stream file Offset'])
                    break


        #Find ChunkStoreUID
        UIDs = self.fs.listdir("/System Volume Information/Dedup/ChunkStore/")
        
        #Calculate All Streams Offset.
        target = {}
        print("  [+] Finding Deleted Stream Files")
        cnt = 0
        for uid in UIDs:
            stream_dir = self.fs.fsobj.open_dir(path="/System Volume Information/Dedup/ChunkStore/"+uid.decode()+"/Stream/")
            count = 0
            for fobj in stream_dir:
                count +=1
                if bytes(".ccc",encoding='utf8') not in fobj.info.name.name:
                    continue
                streamfile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/"+uid.decode()+"/Stream/"+fobj.info.name.name.decode('utf8'))
                exists  = FS.get_AllstreamObj(streamfile)
                if uid.decode()[1:-5] in streams_inuse.keys():
                    if fobj.info.name.name.decode('utf8') in streams_inuse[uid.decode()[1:-5]].keys():
                        offsets = streams_inuse[uid.decode()[1:-5]][fobj.info.name.name.decode()]
                        for offset in offsets:
                            if str(offset) in exists.keys():
                                del exists[str(offset)]
                if uid.decode() not in target.keys():
                    target[uid.decode()] ={}
                target[uid.decode()][fobj.info.name.name.decode()] = exists
                cnt += len(target[uid.decode()][fobj.info.name.name.decode()])
        print(f"      [-] Found {cnt} Deleted Streams")
        
        print("  [+] Recovering Data Files.")
        count =0
        for guid in target.keys():
            for stmfile in target[guid].keys():
                for name,_streams in target[guid][stmfile].items():
                    cumul = 0       
                    name = "OFFSET_"+name
                    fp = open("\\".join([self.outPath,name.replace(chr(0),"")]),'wb')
                    for _stream in _streams:
                        datafile = self.fs.fsobj.open("/System Volume Information/Dedup/ChunkStore/{"+rundata['Chunkstore UID']+"}.ddp/Data/"+_stream['Data File Name'])
                        data = FS.parse_datafile(datafile,_stream)
                        if type(data) == int:
                            flag = 1
                            print("ERROR Reading Data File. ERRORCODE :"+str(data))
                            break
                        #Cumulative ChunkSize Check!
                        cumul += len(data)
                        if cumul != _stream['Cumulative Chunk Size']:
                            print("     [-] Warning : INVALID Cumulative Chunk Size")
                            print("     [-] File name : "+str(name.replace(chr(0),"")))
                            fp.close()
                            os.remove("\\".join([self.outPath,name.replace(chr(0),"")]))
                            break
                        fp.write(data)
                    fp.close()
                    count +=1
                    #write file metadata
        self.end = time.time()
        return count 


if __name__ == "__main__":
    args = start()
    #Assemble - Extract
    if args.all == True:
        #create output dir
        outputDir = "\\".join([args.outdir,'AllDedupFiles'])
        if os.path.exists(outputDir)==False:
            os.mkdir(outputDir)
        
        #parse all
        a = Assemble(args.input,outputDir)
        success = a.assemble_all()
        print("\n  [+] Finished.")
        dedup_statistic(success,a.total,a.end-a.start)    
    if args.filename != None:
        #create output dir
        outputDir = "\\".join([args.outdir,'DedupFiles'])
        if os.path.exists(outputDir)==False:
            os.mkdir(outputDir)
        
        #parse by file
        f = Assemble(args.input,outputDir)
        success = 0
        for file in args.filename:
            res = f.assemble_file(file)
            if  res == -1:
                print("     [-] Target File Not Found.")
                print("     [-] It may exist but not a deduplicated file.")
                print("     [-] Passing....")
            else:
                success += 1
            
        print("\n  [+] Finished.")
        dedup_statistic(success,len(args.filename),f.end-f.start)

        #write file info
    
    #Recovery
    if args.carve == True:
        print("UNSUPPORTED")
    if args.runlist == True:
        #create output dir
        outputDir = "\\".join([args.outdir,'Carved_By_DataRun'])
        if os.path.exists(outputDir)==False:
            os.mkdir(outputDir)
        a = Recover(args.input,args.outdir)
        success = a.carve_DataRun()
        print("\n  [+] Finished.")
        dedup_statistic(success,a.total,a.end-a.start)    
    if args.stream == True:
        #create output dir
        outputDir = "\\".join([args.outdir,'Carved_By_DataRun'])
        if os.path.exists(outputDir)==False:
            os.mkdir(outputDir)
        a = Recover(args.input,args.outdir)
        success = a.carve_Stream()
        print("\n  [+] Finished.")
        dedup_statistic(success,a.total,a.end-a.start)    
