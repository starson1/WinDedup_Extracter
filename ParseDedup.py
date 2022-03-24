import time


import Dedup_Structure as DS

MFT_PATH = "./File/$MFT"
RAW_IMAGE_PATH = r"F:\#My_Work\WinServer2019\dumps\Dump_1101_OtherFile Added.001"
R_FILEPATH = "./File/$R"
DATAFILE_PATH = "./File/00000001.00000001.ccc"
STREAMFILE_PATH = "./File/00010000.00000001.ccc"

CLUSTER_SIZE= 0x200

class DedupAssemble:
    def __init__(self,filepath):
        self.filepath = filepath
        self.filename = "" ####GET FILENAME!!
        self.run()

    def run(self):
        start = time.time()

        #Read $R back index
        fp = open(self.filepath,'rb')
        Record = self.read_R(fp)
        fp.close()

        #Get MFT information
        reparse = []
        fp = open(".\File\$MFT",'rb')
        for rec in Record:
            if rec['Reparse Tag'] != b"\x13\x00\x00\x80":
                print("ERROR")
                continue
            reparse.append(self.read_MFT_attribute(fp,rec['MFT address']))
        fp.close()
        
        #Read Run Data
        rundata=[]
        fp = open(RAW_IMAGE_PATH,'rb') # open whole filesystem just for now, will be replaced with libewf
        for i in reparse:
            tmp = self.read_DataRun(fp,i['RUN1'])
            tmp['FileName'] = i['FileName']
            rundata.append(tmp)
        fp.close()

        #Read Stream File & Datafile --> Assemble Process
        count = 1
        for i in rundata:
            filename = str(i['FileName'].replace(b'\x00',b'')).replace("b'","").replace("'","")
            outputfile = b""
            stream = self.read_Streamfile(i)
            if type(stream) == int:
                print("ERROR READING StreamFile ERRORCODE : "+str(stream))
                continue
            for j in stream:
                data = self.read_Datafile(j)
                if type(data) == int:
                    print("ERROR Reading Data File. ERRORCODE :"+str(data))
                    continue
                outputfile += data
                #CUMULATIVE CHUNKSIZE CHECK!!
            if filename != "":
                fp = open("./RESULT/"+filename,'wb')
                count +=1
            else:
                fp = open('./RESULT/CARVEDFILE'+str(count),'wb')
                count +=1
            fp.write(outputfile)
            fp.close()
        
        end = time.time()
        
        # Statistics
        print("")
        print("[+]Total Deduplicated File Count : " + str(len(Record)))
        print("[+]Total Reassembled File Count : "+str(count-1))
        print("[+]Reassemble Rate : "+str(100*(count-1)/len(Record))+"%")
        print("[+]Elapsed Time : "+ str(end-start))
        print("")

    def read_R(self,handle):
        data = handle.read()
        res = DS.parse_R(data)
        
        offset = res['Entry Offset']
        Record = []
        
        for i in range(0,(res['Entry Size'] // 0x20 )):
            record_data = data[offset:offset+0x20]
            if record_data[0x10:0x14] != b"\x13\x00\x00\x80":
                continue
            Record.append(DS.parse_Record(record_data))
            offset += 0x20
        return Record   
    def read_MFT_attribute(self,handle,offset):
        handle.seek(offset)
        data = handle.read(0x400)
        mft = DS.parse_MFT(data)

        res = DS.parse_Reparse(mft['$REPARSE_POINT'])
        filename= self.get_Filename(mft['$FILE_NAME'])
        res['FileName'] = filename

        return res
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
            stream_data.append(DS.parse_streamdata(stmd))
        
        return stream_data
    def read_Datafile(self,stream):
        fp = open("File/"+stream['Data File Name'],'rb')
        fp.seek(stream['Data Offset'])
        data = fp.read(0x58)
        chunk_info = DS.parse_Datachunk(data)
        
        #VALIDATION!!!        
        if chunk_info['Chunk Number'] != stream['Chunk Number']: return -1
        if chunk_info['Data Hash'] != stream['Hash']: return -2
        if chunk_info['Chunk Size'] !=stream['Chunk Size']: return -3

        fp.seek(stream['Data Offset']+0x58)
        chunk_data = fp.read(chunk_info['Chunk Size'])
        fp.close()

        return chunk_data
    def get_Filename(self,attr):
        namelen = attr[0x50]
        name = attr[0x5A:]
        return name
        

        

if __name__ == "__main__":
    a = DedupAssemble(R_FILEPATH) 