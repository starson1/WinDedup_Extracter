## Used for Windows Server 2016,2019,2022
## Made by vared -> vared.kr
## Tested on Windows Server 2019
## Deduplicated file Recovery Tool
## Requirments : Image File,extracted System Volume Information directory
import sys,os
import struct
from tqdm import trange
from tqdm import tqdm
from optparse import OptionParser
from datetime import datetime



def chkpath(path):
    if not os.path.exists(path+'System Volume Information'):
        print("Not a Valid Path. Your Filesystem must be NTFS")
        exit()

def parse_Reparse(attr):
    ret={}
    ret['Signatrue'] = attr[:0x4]
    ret['Size'] = struct.unpack('<L',attr[0x4:0x8])[0]
    ret['Resident Flag'] = attr[0x8]
    ret['Name Length'] = attr[0x9]
    ret['Name Offset'] = struct.unpack('<H',attr[0xA:0xC])[0]
    ret['Flags'] = struct.unpack('<H',attr[0xC:0xE])[0]
    ret['Attribute ID'] = struct.unpack('<H',attr[0xE:0x10])[0]
    ret['Data Run Offset'] = struct.unpack('<H',attr[0x20:0x22])[0]
    ret['Compression'] = struct.unpack('<H',attr[0x22:0x24])[0]
    ret['Padding'] = struct.unpack('<L',attr[0x24:0x28])[0]
    ret['Alloc Size'] = struct.unpack('<Q',attr[0x28:0x30])[0]
    ret['Real Size'] = struct.unpack('<Q',attr[0x30:0x38])[0]
    ret['Init Size'] = struct.unpack('<Q',attr[0x38:0x40])[0]
    return ret
def parse_Dedup(dat):
    ret = {}
    ret['Reparse Tag'] = dat[:0x4]
    ret['Size'] = dat[0x4:0x8]

    ret['FeRp'] = dat[0x0C:0x10]
    ret['FeRp CRC'] = dat[0x10:0x14]
    ret['FeRp Size'] = dat[0x14:0x18:]
    ret['Chunkstore UID'] = (dat[0x6C:0x70][::-1].hex() +"-"+ dat[0x70:0x72][::-1].hex() +"-"+dat[0x72:0x74][::-1].hex()+"-"+ dat[0x74:0x76].hex()+"-"+dat[0x76:0x7C].hex()).upper()
    ret['File Creation time'] = datetime.fromtimestamp(struct.unpack('<Q',dat[0x7C:0x84])[0]//10000000 - 11644473600).strftime('%Y-%m-%d %H:%M:%S')
    ret['Original File Size'] = dat[0x84:0x88]
    
    for i in range(0x88,len(dat)):
        if dat[i:i+4] == b'RbRp':
            break
    ret['RbRp'] = dat[i:i+0x4]
    ret['RbRp CRC'] = dat[i+0x4:i+0x8]
    ret['RbRp Size'] = struct.unpack('<L',dat[i+0x8:i+0xC])[0]
    
    i +=ret['RbRp Size']
    ret['DdRp'] = dat[i:i+0x4]
    ret['DdRp CRC'] = dat[i+0x4:i+0x8]
    ret['DdRp Size'] = struct.unpack('<L',dat[i+0x8:i+0xC])[0]
    ret['Stream file name1'] = (str(dat[i+0x30:i+0x34][::-1])+"."+str(dat[i+0x28:i+0x2C][::-1])).replace("bytearray(b'","").replace(")","").replace("\\x","").replace('\'','')+".ccc"
    ret['Hash Stream number1'] = struct.unpack('<L',dat[i+0x2C:i+0x30])[0]
    ret['Stream file name2'] = (str(dat[i+0x38:i+0x3C][::-1])+"."+str(dat[i+0x40:i+0x44][::-1])).replace("bytearray(b'","").replace(")","").replace("\\x","").replace('\'','')+".ccc"
    ret['Hash Stream number2'] = struct.unpack('<L',dat[i+0x34:i+0x38])[0]
    ret['Stream file Offset'] = struct.unpack('<L',dat[i+0x3C:i+0x40])[0]
    ret['SMAP Size'] = struct.unpack('<L',dat[i+0x4C:i+0x50])[0]
    ret['Hash'] = dat[i+0x54:i+0x64]
    ret['File Size'] = struct.unpack('<L',dat[i+0x64:i+0x68])[0]
    
    i += ret['DdRp Size']
    ret['CRC'] = dat[i:i+4]
    return ret
def parse_streamheader(dat):
    ret = {}
    ret['Signature']=dat[0x00:0x08]
    ret['Hash Stream Number']=struct.unpack('<L',dat[0x08:0x0C])[0]
    ret['SMAP size']=struct.unpack('<L',dat[0x0C:0x10])[0]
    ret['Stream Hash']=dat[0x38:0x48]
    ret['SMAP Signature'] = dat[0x68:0x70]
    return ret
def parse_streamdata(dat):
    ret = {}
    ret['Chunk Number'] = dat[0x00:0x04]
    ret['Data File Name'] = str(dat[0x04:0x08][::-1]).replace('bytearray(b\'','').replace('\')',"").replace("\\","").replace('x','') + "." + str(dat[0x0C:0x10][::-1]).replace('bytearray(b\'','').replace('\')',"").replace("\\","").replace('x','')
    ret['Data Offset'] = struct.unpack('<L',dat[0x08:0x0C])[0]
    ret['Cumulative Chunk Size'] = struct.unpack('<L',dat[0x10:0x14])[0]
    ret['Chunk Size'] = struct.unpack('<L',dat[0x38:0x3C])[0]
    ret['Hash'] = dat[0x18:0x38]
    return ret

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
        rep_tmp = parse_Reparse(reparse_dict[key][0])        
        if rep_tmp['Size'] == 0x48:
            if rep_tmp['Resident Flag'] == 1:
                #calc Run List Offset
                DatRun = reparse_dict[key][0][rep_tmp['Data Run Offset']:]
                datlen = DatRun[0] // 16
                size = DatRun[0] % 16
                runoffset = int.from_bytes(bytes(DatRun[2:2+datlen]),byteorder='little') * 0x1000 # cluster size must be 0x1000..!
                #New Structure!
                RunData = data[runoffset:runoffset+rep_tmp['Real Size']]
                dup_tmp = parse_Dedup(RunData)
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
                s_header = parse_streamheader(s_data[rundata['Stream file Offset']:rundata['Stream file Offset']+0x70])
                if rundata['Hash Stream number1'] == s_header['Hash Stream Number']:
                    if rundata['SMAP Size'] == s_header['SMAP size']:
                        if rundata['Hash'] == s_header['Stream Hash']:
                            if s_header['SMAP Signature'] == b'Smap\x01\x04\x04\x01':
                                #get chunk data
                                chunk_num = int((s_header['SMAP size'] - 8) / 0x40)
                                cumul_size = 0
                                ret_data = b''
                                for i in trange(1,chunk_num+1):
                                    dat = parse_streamdata(s_data[rundata['Stream file Offset']+0x70+0x40*(i-1):rundata['Stream file Offset']+0x70 +0x40*(i)])
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

def mode2_RecoverDedup(path):
    print('mode 2')

if __name__ == "__main__":
    
    if(len(sys.argv) <= 1):
        print("-h option shows user manual")
        exit()
    use = "python %prog [options] raw_file"
    parser = OptionParser(usage = use)    
    parser.add_option("-m", "--mode",dest="selectMode",default=False,type='string',
                    help="Select Mode(1,2)")
    parser.add_option("-t", "--test",dest="nothing",default=False,type='string',
                    help="Test Option")
    (options,args) = parser.parse_args()
    if args == []:
        print("No File Input Given")
        exit()
    if options.selectMode:
        drivepath = os.path.abspath(args[0])
        if options.selectMode == '1':
            mode1_ParseDedup(drivepath)
        elif options.selectMode == '2':
            mode2_RecoverDedup(drivepath)
        else:
            print("Unsupported Mode")
        


    
    
    
    

