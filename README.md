
Parsing files from Deduplicated volumes. It can also recover deleted files from NTFS Filesystem that were deduplicated.


## Installation

    git clone https://github.com/starson1/WinDedup_Extracter

## Usage
    python windedup.py [options] imagefile
    ex) python windedup.py -m 1 test.001
Needs 

  1) "Raw" Image File
  
  2) System Volume Information Directory exported from image file

      ex) WinDedup_Extracter/System Volume Information

  
  Supporting E01, Raw, AD1  --> TBA
  

Structure of System Volume Information:

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
       

## Documentation on APFS

- [**TBA**](url): Paper where WinDedup is presented.
- [**Forensic analysis of deduplication file systems**](https://www.sciencedirect.com/science/article/pii/S1742287617300324)
- [**A Study of Method to Restore Deduplicated Files in Windows Server 2012**](https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=JAKO201706749670643&dbt=NART)

