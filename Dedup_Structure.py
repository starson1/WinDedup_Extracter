import struct
from datetime import datetime
from sys import byteorder

END_SIGNATURE = b"\xff\xff\xff\xff"
MFT_RECORD_SIZE = 0x400

def parse_MFT(data):
    ret = {}
    ret['Signature'] = data[:0x04]
    ret['Seq Num'] = data[0x10:0x12]
    ret['Offset to Attribute'] = struct.unpack('<H',data[0x14:0x16])[0]
    ret['Entry Number'] = struct.unpack('<L',data[0x2C:0x30])[0]

    attr_ID = ""
    offset = ret['Offset to Attribute']
    while attr_ID != END_SIGNATURE:
        attr_ID = data[offset:offset+0x04]
        attr_len = struct.unpack("<L",data[offset+0x04:offset+0x08])[0]
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
    ret['Size'] = struct.unpack('<L',attr[0x4:0x8])[0]
    ret['Non-Resident Flag'] = attr[0x8]
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
    ret['Stream file name1'] = (str(dat[i+0x30:i+0x34][::-1])+"."+str(dat[i+0x28:i+0x2C][::-1])).replace("bytearray(b\'","").replace(")","").replace('b','').replace("\\x","").replace('\'','')+".ccc"
    ret['Hash Stream number1'] = struct.unpack('<L',dat[i+0x2C:i+0x30])[0]
    ret['Stream file name2'] = (str(dat[i+0x38:i+0x3C][::-1])+"."+str(dat[i+0x40:i+0x44][::-1])).replace("bytearray(b\'","").replace(")","").replace('b','').replace("\\x","").replace('\'','')+".ccc"
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
    ret['SMAP Size']=struct.unpack('<L',dat[0x0C:0x10])[0]
    ret['Stream Hash']=dat[0x38:0x48]
    ret['SMAP Signature'] = dat[0x68:0x70]
    return ret
def parse_streamdata(dat):
    ret = {}
    ret['Chunk Number'] = int.from_bytes(dat[0x00:0x04],byteorder='little')
    ret['Data File Name'] = dat[0x04:0x08][::-1].hex() + "." + dat[0x0C:0x10][::-1].hex()+".ccc"
    ret['Data Offset'] = struct.unpack('<L',dat[0x08:0x0C])[0]
    ret['Cumulative Chunk Size'] = struct.unpack('<L',dat[0x10:0x14])[0]
    ret['Chunk Size'] = struct.unpack('<L',dat[0x38:0x3C])[0]
    ret['Hash'] = dat[0x18:0x38]
    return ret
def parse_Datachunk(dat):
    ret = {}
    ret['Signature'] = dat[0x00:0x08]
    ret['Chunk Number'] = int.from_bytes(dat[0x08:0x0C],byteorder='little')
    ret['Chunk Size'] = int.from_bytes(dat[0x0C:0x10],byteorder='little')
    ret['Compression Flag'] = dat[0x0C]
    ret['Data Hash'] = dat[0x28:0x48]

    return ret
def parse_R(dat):
    ret = {}
    ret['Signature'] = dat[0x00:0x04]
    ret['Entry Offset'] = struct.unpack('<L',dat[0x18:0x1C])[0] + 0x18
    ret['Entry Size'] = (struct.unpack('<L',dat[0x1C:0x20])[0]) - 0x38

    return ret
def parse_Record(dat):
    ret = {}
    ret["Reparse Tag"] = dat[0x10:0x14]
    ret["Seq Num"] =dat[0x1A:0x1C]
    ret["MFT Key Reference"] = dat[0x14:0x1A]
    ret["MFT address"] =Find_MFT_Record(dat[0x14:0x18])

    return ret

def Find_MFT_Record(key_ref:bytes):
        return int.from_bytes(key_ref,byteorder='little') * MFT_RECORD_SIZE