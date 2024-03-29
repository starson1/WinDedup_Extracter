import LZ77

END_SIGNATURE = b"\xff\xff\xff\xff"
MFT_RECORD_SIZE = 0x400
CLUSTER_SIZE = 0x200

def parse_MFTattr(data):   
    ret = {}
    ret['Signature'] = data[:0x05]
    if data[:0x05] != b"FILE0": 
        return None
    ret['Seq Num'] = data[0x10:0x12]
    ret['Flags'] = int.from_bytes(data[0x16:0x18], byteorder='little')
    ret['Offset to Attribute'] = int.from_bytes(data[0x14:0x16],byteorder='little')
    ret['Entry Number'] = int.from_bytes(data[0x2C:0x30],byteorder='little')

    attr_ID = ""
    offset = ret['Offset to Attribute']
    while attr_ID != END_SIGNATURE:
        attr_ID = data[offset:offset+0x04]
        attr_len = int.from_bytes(data[offset+0x04:offset+0x08],byteorder='little')
        attr_data = data[offset:offset+attr_len]

        if attr_ID == b"\x10\x00\x00\x00":
            attr_name = "$STANDARD_INFORMATION"
            ret[attr_name] = attr_data
        if attr_ID == b"\x20\x00\x00\x00":
            attr_name = "$ATTRIBUTE_LIST"
            ret[attr_name] = attr_data
        if attr_ID == b"\x30\x00\x00\x00":
            attr_name = "$FILE_NAME"
            ret[attr_name] = attr_data
        if attr_ID == b"\x40\x00\x00\x00":
            attr_name = "$OBJECT_ID"
            ret[attr_name] = attr_data
        if attr_ID == b"\x50\x00\x00\x00":
            attr_name = "$SECURITY_DESCRIPTOR"
            ret[attr_name] = attr_data
        if attr_ID == b"\x60\x00\x00\x00":
            attr_name = "$VOLUME_NAME"
            ret[attr_name] = attr_data
        if attr_ID == b"\x70\x00\x00\x00":
            attr_name = "$VOLUME_INFORMATION"
            ret[attr_name] = attr_data
        if attr_ID == b"\x80\x00\x00\x00":
            attr_name = "$DATA"
            ret[attr_name] = attr_data
        if attr_ID == b"\x90\x00\x00\x00":
            attr_name = "$INDEX_ROOT"
            ret[attr_name] = attr_data
        if attr_ID == b"\xA0\x00\x00\x00":
            attr_name = "$INDEX_ALLOCATION"
            ret[attr_name] = attr_data
        if attr_ID == b"\xB0\x00\x00\x00":
            attr_name = "$BITMAP"
            ret[attr_name] = attr_data
        if attr_ID == b"\xC0\x00\x00\x00":
            attr_name = "$REPARSE_POINT"
            ret[attr_name] = attr_data
        offset += attr_len
    return ret
def parse_Reparse(attr):
    ret={}
    ret['Signatrue'] = attr[:0x4]
    ret['Size'] = int.from_bytes(attr[0x4:0x8],byteorder='little')
    ret['Non-Resident Flag'] = attr[0x8]
    ret['Name Length'] = attr[0x9]
    ret['Name Offset'] = int.from_bytes(attr[0xA:0xC],byteorder='little')
    ret['Flags'] = int.from_bytes(attr[0xC:0xE],byteorder='little')
    ret['Attribute ID'] = int.from_bytes(attr[0xE:0x10],byteorder='little')
    ret['Data Run Offset'] = int.from_bytes(attr[0x20:0x22],byteorder='little')
    ret['Compression'] = int.from_bytes(attr[0x22:0x24],byteorder='little')
    ret['Padding'] = int.from_bytes(attr[0x24:0x28],byteorder='little')
    ret['Alloc Size'] = int.from_bytes(attr[0x28:0x30],byteorder='little')
    ret['Real Size'] = int.from_bytes(attr[0x30:0x38],byteorder='little')
    ret['Init Size'] = int.from_bytes(attr[0x38:0x40],byteorder='little')

    meta_offset = ret['Data Run Offset']
    data_run = []
    count =1
    while attr[meta_offset] != 0:
        ll = attr[meta_offset] % 16
        lo = attr[meta_offset] // 16
        length = int.from_bytes(attr[meta_offset+1:meta_offset+1+ll],byteorder='little')
        offset = int.from_bytes(attr[meta_offset+1+ll:meta_offset+1+ll+lo],byteorder='little')
        ret['RUN'+str(count)] = (length,offset)
        meta_offset+= (ll+ lo+1)
        count +=1
        
    return ret
def parse_Dedup(dat):
    ret = {}
    ret['Reparse Tag'] = dat[:0x4]
    ret['Size'] = dat[0x4:0x8]

    ret['FeRp'] = dat[0x0C:0x10]
    ret['FeRp CRC'] = dat[0x10:0x14]
    ret['FeRp Size'] = dat[0x14:0x18:]
    ret['Chunkstore UID'] = (dat[0x6C:0x70][::-1].hex() +"-"+ dat[0x70:0x72][::-1].hex() +"-"+dat[0x72:0x74][::-1].hex()+"-"+ dat[0x74:0x76].hex()+"-"+dat[0x76:0x7C].hex()).upper()
    #ret['File Creation time'] = datetime.fromtimestamp(int.from_bytes(dat[0x7C:0x84])//10000000 - 11644473600).strftime('%Y-%m-%d %H:%M:%S')
    ret['Original File Size'] = dat[0x84:0x88]
    
    for i in range(0x88,len(dat)):
        if dat[i:i+4] == b'RbRp':
            break
    ret['RbRp'] = dat[i:i+0x4]
    ret['RbRp CRC'] = dat[i+0x4:i+0x8]
    ret['RbRp Size'] = int.from_bytes(dat[i+0x8:i+0xC],byteorder='little')
    
    i +=ret['RbRp Size']
    ret['DdRp'] = dat[i:i+0x4]
    ret['DdRp CRC'] = dat[i+0x4:i+0x8]
    ret['DdRp Size'] = int.from_bytes(dat[i+0x8:i+0xC],byteorder='little')
    #ret['Stream file name1'] = (str(dat[i+0x30:i+0x34][::-1])+"."+str(dat[i+0x28:i+0x2C][::-1])).replace("bytearray(b\'","").replace(")","").replace('b','').replace("\\x","").replace('\'','')+".ccc"
    ret['Hash Stream number1'] = int.from_bytes(dat[i+0x2C:i+0x30],byteorder='little')
    #ret['Stream file name2'] = (str(dat[i+0x38:i+0x3C][::-1])+"."+str(dat[i+0x40:i+0x44][::-1])).replace("bytearray(b\'","").replace(")","").replace('b','').replace("\\x","").replace('\'','')+".ccc"
    ret['Hash Stream number2'] = int.from_bytes(dat[i+0x34:i+0x38],byteorder='little')
    ret['Stream file Offset'] = int.from_bytes(dat[i+0x3C:i+0x40],byteorder='little')
    ret['SMAP Size'] = int.from_bytes(dat[i+0x4C:i+0x50],byteorder='little')
    ret['Hash'] = dat[i+0x54:i+0x64]
    ret['File Size'] = int.from_bytes(dat[i+0x64:i+0x68],byteorder='little')
    
    i += ret['DdRp Size']
    ret['CRC'] = dat[i:i+4]
    return ret
def parse_streamheader(dat):
    ret = {}
    ret['Signature']=dat[0x00:0x08]
    ret['Hash Stream Number']=int.from_bytes(dat[0x08:0x0C],byteorder='little')
    ret['SMAP Size']=int.from_bytes(dat[0x0C:0x10],byteorder='little')
    ret['Stream Hash']=dat[0x38:0x48]
    ret['SMAP Signature'] = dat[0x68:0x70]
    return ret
def parse_streamdata(dat):
    ret = {}
    ret['Chunk Number'] = int.from_bytes(dat[0x00:0x04],byteorder='little')
    if ret['Chunk Number'] == 0:
        return None
    ret['Data File Name'] = dat[0x04:0x08][::-1].hex() + "." + dat[0x0C:0x10][::-1].hex()+".ccc"
    ret['Data Offset'] = int.from_bytes(dat[0x08:0x0C],byteorder='little')
    ret['Cumulative Chunk Size'] = int.from_bytes(dat[0x10:0x14],byteorder='little')
    ret['Chunk Size'] = int.from_bytes(dat[0x38:0x3C],byteorder='little')
    ret['Hash'] = dat[0x18:0x38]
    return ret
def parse_Datachunk(dat):
    ret = {}
    ret['Signature'] = dat[0x00:0x08]
    ret['Chunk Number'] = int.from_bytes(dat[0x08:0x0C],byteorder='little')
    ret['Chunk Size'] = int.from_bytes(dat[0x0C:0x10],byteorder='little')
    ret['Compression Flag'] = dat[0x20]
    ret['Data Hash'] = dat[0x28:0x48]

    return ret
def parse_R(dat):
    ret = {}
    ret['Signature'] = dat[0x00:0x04]
    ret['Entry Offset'] = int.from_bytes(dat[0x18:0x1C],byteorder='little') + 0x18
    ret['Entry Size'] = (int.from_bytes(dat[0x1C:0x20],byteorder='little')) - 0x38
    
    if ret['Signature'] == b"\x00\x00\x00\x00":
        ret['Entry Offset'] = 0x20
        ret['Entry Size'] = len(dat)-0x20

    return ret
def parse_Record(dat):
    ret = {}
    ret["Reparse Tag"] = dat[0x10:0x14]
    ret["Seq Num"] =dat[0x1A:0x1C]
    ret["MFT Key Reference"] = dat[0x14:0x1A]
    ret["MFT address"] =Find_MFT_Record(dat[0x14:0x18])

    return ret
def parse_DeleteLog(dat):
    ret = {}
    #Header
    ret['Signature'] = dat[0x00:0x08]
    ret['CRC-32'] = dat[0x0C:0x10]
    #Data
    offset = 0x10
    records =[]
    while offset <= len(dat):
        record = {}
        record['Hash Stream Number'] = int.from_bytes(dat[offset:offset+0x04],byteorder='little')
        record['Hash'] = dat[offset+0x04:offset+0x14]
        if record['Hash'] != b"" and record['Hash Stream Number'] != b"":
            records.append(record)
        offset += 0x28
    ret['Records'] = records
    return ret 
def parse_MFT(handle,offset):
    mftattr = parse_MFTattr(handle.read_random(offset,0x400))
    res = parse_Reparse(mftattr['$REPARSE_POINT'])
    try:
        res['FileName'] = mftattr['$FILE_NAME'][0x5A:].decode('utf8')
    except:
        res['FileName'] = mftattr['$FILE_NAME'][0x5A:].decode('utf16')

    return res
def parse_DataRun(handle,run):
    data = handle.read(run[1]*0x1000,CLUSTER_SIZE * run[0])
    return parse_Dedup(data)
def parse_datafile(handle,stream):
    data = handle.read_random(stream['Data Offset'],0x48)
    chunk_info = parse_Datachunk(data)
    
    #VALIDATION!!!        
    if chunk_info['Chunk Number'] != stream['Chunk Number']: return -1
    if chunk_info['Data Hash'] != stream['Hash']: return -2
    if chunk_info['Chunk Size'] !=stream['Chunk Size']: return -3
    
    chunk_data = handle.read_random(stream['Data Offset']+0x5C-0x04,chunk_info['Chunk Size'])
    prev_chunk = chunk_data

    if chunk_info['Compression Flag'] == 2:
        #LZ77 inflate
        #compressor = LZ77.LZ77Compressor()
        #chunk_data  = compressor.decompress(chunk_data)
        return chunk_data,1
    return chunk_data,0
def get_AllstreamObj(handle):
    res= {}
    i = 0
    while(i < handle.info.meta.size):
        sign = handle.read_random(i,8)
        if sign == b"\x43\x6B\x68\x72\x01\x03\x03\x01":
            try:
                header = handle.read_random(i,0x70)
            except:
                return 0,None
            stream_hdr = parse_streamheader(header)
            #Calculate SMAP
            num = (stream_hdr['SMAP Size'] - 8) // 0x40
            #Read Stream Data
            stream_data = []
            for j in range(0,num):
                stmd = handle.read_random(i+0x70+(0x40 * j),0x40)
                parsed = parse_streamdata(stmd)
                if parsed == None: break
                stream_data.append(parsed)
            if len(stream_data) != 0: res[str(i)]=(stream_data)
        i += 0x10
    return res

def find_streamfile(handle,record):
    try:
        header = handle.read_random(record['Stream file Offset'],0x70)
    except:
        return 0,None
    stream_hdr = parse_streamheader(header)

    #VALIDATION!!!
    if stream_hdr['Signature'] != b"\x43\x6B\x68\x72\x01\x03\x03\x01": return -1,None
    if stream_hdr['Stream Hash'] != record['Hash']: return -2,None
    if stream_hdr['SMAP Size'] != record['SMAP Size'] : return -3,None
    if stream_hdr['Hash Stream Number'] != record['Hash Stream number1']: return -4,None
    #Calculate SMAP
    num = (stream_hdr['SMAP Size'] - 8) // 0x40
    #Read Stream Data
    stream_data = []
    for i in range(0,num):
        stmd = handle.read_random(record['Stream file Offset']+0x70+(0x40 * i),0x40)
        parsed = parse_streamdata(stmd)
        stream_data.append(parsed)
    
    return stream_data,record['FileName']
def Find_MFT_Record(key_ref:bytes):
        return int.from_bytes(key_ref,byteorder='little') * MFT_RECORD_SIZE
