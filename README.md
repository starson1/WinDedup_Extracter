# WinDedup_Extracter_NEW


Parsing files from Deduplicated volumes. It can also recover deleted files from NTFS Filesystem that were deduplicated.


## Installation

    git clone https://github.com/starson1/WinDedup_Extracter

## Usage
    usage: ParseDedup.py [-h] -i INPUT -o OUTDIR [-a] [-f [FILENAME ...]] [-c] [-r] [-s]
    Windows Server Deuplication Extractor/Recovery
    options:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            Input File Path (E01 file)
      -o OUTDIR, --outdir OUTDIR
                            Output Directory for Results
      -a, --all             Extract All Deduplicated Files
      -f [FILENAME ...], --filename [FILENAME ...]
                            Extract By Filename (Multi-Input Allowed)
      -c, --carve           Carve Searching Unallocated Area (Unsupported)
      -r, --runlist         Recovery Using Runlist Structure (Unallocated Area)
      -s, --stream          Recovery Using Stema File (Allocated Area)
## Needs 

  1) E01 image file
  

## Structure of System Volume Information:

    System Volume Information
    ├─ Dedup                 
    │  ├─ ChunkStore                  
    │  │  ├─ {GUID}.ddp
    │  │      ├─ Data
    │  │      ├─ HotSpot
    │  │      ├─ Stream 
    │  │      └─ …
    │  ├─ Logs                
    │  │  └─ …
    |  ├─ Settings
    │  │  └─ …
    |  ├─ State
    │  │  └─ …
    └─ WPSettings.dat
       

## Documentation on Windows Deduplication

- [**TBA**](url): Paper where WinDedup is presented.
- [**Forensic analysis of deduplication file systems**](https://www.sciencedirect.com/science/article/pii/S1742287617300324)
