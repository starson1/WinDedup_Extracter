from dfvfs.lib import definitions
from dfvfs.path import factory
from dfvfs.resolver import resolver

IMAGEFILEPATH = "C:/Users/stars/Desktop/files/Final_Testset.001"


location = IMAGEFILEPATH

os_path_spec = factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_OS, location=location)
ewf_path_spec = factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_EWF, parent=os_path_spec)
tsk_partition_path_spec = factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p1', parent=ewf_path_spec)
tsk_path_spec = factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_TSK, location='/', parent=tsk_partition_path_spec)

file_entry = resolver.Resolver.OpenFileEntry(tsk_path_spec)

for sub_file_entry in file_entry.sub_file_entries:
  print(sub_file_entry.name)