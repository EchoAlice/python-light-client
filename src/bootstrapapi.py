from containers import BeaconBlockHeader, LightClientBootstrap, SyncCommittee
from updatesapi import initialize_block_header, initialize_sync_committee
from helper import (call_api,
                    parse_hex_to_byte,
                    parse_list
)


#                                 =================================
#                                 CREATE BOOTSTRAP CONTAINER OBJECT
#                                 =================================

checkpoint_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/finalized/finality_checkpoints"
checkpoint = call_api(checkpoint_url).json()
finalized_checkpoint_root = checkpoint['data']['finalized']['root']  

trusted_block_root =  parse_hex_to_byte("0xd475339cea53c7718fd422d6583e4c1700d7492f94b5b83cf871899b2701846b")

bootstrap_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/light_client/bootstrap/0xd475339cea53c7718fd422d6583e4c1700d7492f94b5b83cf871899b2701846b" 
bootstrap = call_api(bootstrap_url).json()

bootstrap_header_message = bootstrap['data']['header']
bootstrap_block_header = initialize_block_header(bootstrap_header_message)

bootstrap_committee_message = bootstrap['data']['current_sync_committee']
bootstrap_sync_committee = initialize_sync_committee(bootstrap_committee_message)

bootstrap_sync_committee_branch = bootstrap['data']['current_sync_committee_branch']
parse_list(bootstrap_sync_committee_branch) 

bootstrap_object = LightClientBootstrap(
  header= bootstrap_block_header,
  current_sync_committee= bootstrap_sync_committee,
  current_sync_committee_branch= bootstrap_sync_committee_branch
)