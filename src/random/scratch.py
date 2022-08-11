def get_sync_period(slot_number):
  sync_period = slot_number // 8192
  return sync_period

def get_subtree_index(generalized_index: int) -> int:
  return int(generalized_index % 2**5) 

#  TO DO:
#
#     Merge bootstrapapi with updateapi



#                                                         \\\\\\\\////////
#                                                          ==============
#                                                             TEST ZONE  
#                                                          ==============
#                                                         ////////\\\\\\\\
from containers import BeaconBlockHeader, LightClientBootstrap, SyncCommittee
from api import initialize_block_header, initialize_sync_committee
from helper import (call_api,
                    parse_hex_to_byte,
                    parse_list,
)


#                                 =================================
#                                 CREATE BOOTSTRAP CONTAINER OBJECT
#                                 =================================







# What I know about attested_header but:
#    - The attested header is 75 slots ahead of finalized header. 
#    - They're within the same sync period
#    - The data is organized properly
#    - 
#    
#
#  Maybe this isn't a bug at all? Before the new updated spec, 
#  the finalized header was the header being checked
