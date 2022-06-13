# WinDedup_Extracter_NEW


Parsing files from Deduplicated volumes. It can also recover deleted files from NTFS Filesystem that were deduplicated.


## Installation

    git clone https://github.com/starson1/WinDedup_Extracter

## Usage
    python windedup.py [options] imagefile
    ex) python main.py -m 1 test.001
Needs 

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
