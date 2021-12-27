from tqdm import trange
from tqdm import tqdm
import struct
import os

import Dedup_Structure as DS

def mode1_ParseDedup(path):
    print('[*] Part 1 started')
    #Read Image
    fp = open(path,'rb')
    data = bytearray(fp.read())
    fp.close()
    #Read MFT
    reparse_dict = {}
    for i in trange(0x2000,len(data),0x400):
        if data[i:i+5] == b'FILE0': # Check For MFT Entry
            size = data[i+0x18:i+0x18+2]
            mft_entry = data[i:i+struct.unpack('<H',size)[0]]
            #parse attribute
            attribute = mft_entry[struct.unpack('<H',mft_entry[20:22])[0]:]
            j=0
            filename = ""
            #find Reparse Point Attribute
            while(1):
                try:
                    attr_sign = attribute[j:j+4]
                    attr_size = struct.unpack('<I',attribute[j+4:j+8])[0]
                    if attr_sign == b'\xff\xff\xff\xff':
                        break
                    if attr_sign == b'\x30\x00\x00\x00':
                        filename = attribute[j+0x5A:j+attr_size].decode('utf-16')
                    if attr_sign == b'\xC0\x00\x00\x00':
                        reparse_dict[filename] = [attribute[j:j+attr_size]]
                    j += attr_size
                except:
                    break
    
    #Read Run List & Parse
    print('[*] Part 2 started')
    for key in tqdm(reparse_dict.keys()):        
        rep_tmp = DS.parse_Reparse(reparse_dict[key][0])        
        if rep_tmp['Size'] == 0x48:
            if rep_tmp['Resident Flag'] == 1:
                #calc Run List Offset
                DatRun = reparse_dict[key][0][rep_tmp['Data Run Offset']:]
                datlen = DatRun[0] // 16
                size = DatRun[0] % 16
                runoffset = int.from_bytes(bytes(DatRun[2:2+datlen]),byteorder='little') * 0x1000 # cluster size must be 0x1000..!
                #New Structure!
                RunData = data[runoffset:runoffset+rep_tmp['Real Size']]
                dup_tmp = DS.parse_Dedup(RunData)
                reparse_dict[key].append(dup_tmp)
    
    #Read Stream File
    print('[*] Part 3 started')
    for key in tqdm(reparse_dict.keys()):
        #1. Move to stream file
        rundata = reparse_dict[key][1]
        fp = 0
        if rundata['Stream file name1'] == rundata['Stream file name2']:
            t_path = "./System Volume Information/Dedup"
            if os.path.exists(t_path):
                t_path+='/ChunkStore/'+'{'+rundata['Chunkstore UID']+'}.ddp'
                if os.path.exists(t_path):
                    if os.path.exists(t_path+"/Stream/"+rundata['Stream file name1']):
                        fp = 1
            else:
                print("No Deduplication Folders..! Read requirements")
        #2. check SMAP size, Hash Stream Number,Hash Value, Header Signature
        if fp == 1:
            fp = open(t_path+'/Stream/'+rundata['Stream file name1'],'rb')
            s_data = bytearray(fp.read())
            fp.close()
            if s_data[rundata['Stream file Offset']:rundata['Stream file Offset']+8] == b'Ckhr\x01\x03\x03\x01':
                #stream data validation
                s_header = DS.parse_streamheader(s_data[rundata['Stream file Offset']:rundata['Stream file Offset']+0x70])
                if rundata['Hash Stream number1'] == s_header['Hash Stream Number']:
                    if rundata['SMAP Size'] == s_header['SMAP size']:
                        if rundata['Hash'] == s_header['Stream Hash']:
                            if s_header['SMAP Signature'] == b'Smap\x01\x04\x04\x01':
                                #get chunk data
                                chunk_num = int((s_header['SMAP size'] - 8) / 0x40)
                                cumul_size = 0
                                ret_data = b''
                                for i in trange(1,chunk_num+1):
                                    dat = DS.parse_streamdata(s_data[rundata['Stream file Offset']+0x70+0x40*(i-1):rundata['Stream file Offset']+0x70 +0x40*(i)])
                                    cumul_size += dat['Chunk Size']
                                    if dat['Cumulative Chunk Size'] == cumul_size:
                                        #read data file
                                        try:
                                            fp = open(t_path+'/Data/'+dat['Data File Name']+'.ccc','rb')
                                            chunk_data = bytearray(fp.read())
                                            fp.close()
                                            off = dat['Data Offset']
                                            if chunk_data[off:off+0x8] == b'Ckhr\x01\x03\x03\x01':
                                                if chunk_data[off+0x08:off+0x0C] == dat['Chunk Number']:
                                                    if chunk_data[off+0x28:off+0x48] == dat['Hash']:
                                                        ret_data += chunk_data[off+0x58:off+0x58+struct.unpack('<L',chunk_data[off+0xc:off+0x10])[0]]
                                        except:
                                            continue
                                    else:
                                        print("ERROR...SIZE INCORRECT >>> PASSING....")
                                        break
                                fp = open('./DumpFile'+key.replace('\x00',''),'wb')
                                fp.write(ret_data)
                                fp.close()