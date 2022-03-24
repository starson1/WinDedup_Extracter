## Used for Windows Server 2016,2019,2022
## Made by vared -> vared.kr
## Tested on Windows Server 2019
## Deduplicated file Recovery Tool
## Requirments : Image File,extracted System Volume Information directory
import sys,os
from optparse import OptionParser
import ParseDedup as PD
import RecoverDedup as RD

if __name__ == "__main__":
    if(len(sys.argv) <= 1):
        print("-h option shows user manual")
        exit()
    use = "python %prog [options] raw_file"
    parser = OptionParser(usage = use)    
    parser.add_option("-m", "--mode",dest="selectMode",default=False,type='string',
                    help="Select Mode(1,2)")
    (options,args) = parser.parse_args()
    if args == []:
        print("No File Input Given")
        exit()
    if options.selectMode:
        drivepath = os.path.abspath(args[0])
        if options.selectMode == '1':
            PD.ParseDedup(drivepath)
        elif options.selectMode == '2':
            RD.RecoverDedup(drivepath)
        else:
            print("Unsupported Mode")
        


    
    
    
    

