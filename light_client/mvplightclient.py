import requests
from remerkleable.core import View
from containers import BeaconBlockHeader, SyncCommittee
from merkletreelogic import checkMerkleProof 

# A first milestone for a light client implementation is to HAVE A LIGHT CLIENT THAT SIMPLY TRACKS THE LATEST STATE/BLOCK ROOT.
def callsAPI(url):
  response = requests.get(url)
  json_object = response.json() 
  return json_object

def parseHexToByte(hex_string):
  if hex_string[:2] == '0x':
    hex_string = hex_string[2:]
  byte_string = bytes.fromhex(hex_string)
  return byte_string 

def index_to_path(index):
  path = bin(index)
  if path[:2] == '0b':
    path = path[2:]
  return path

if __name__ == "__main__":
  #                                    
  #                                     \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                      \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                      =========================================
  #                                      INITIALIZATION/BOOTSTRAPPING TO A PERIOD:
  #                                      =========================================
  #                                      ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                     /////////////////// || \\\\\\\\\\\\\\\\\\\\
  #
  #     Get block header at slot N in period X = N // 16384
  #     Ask node for current sync committee + proof of checkpoint root
  #     Node responds with a snapshot
  #     
  #     Snapshot contains:
  #     A. Header- Block's header corresponding to the checkpoint root
  #     
  #           The light client stores a header so it can ask for merkle branches to 
  #           authenticate transactions and state against the header
  #
  #     B. Current sync committee- Public Keys and the aggregated pub key of the current sync committee
  #   
  #           The purpose of the sync committee is to allow light clients to keep track
  #           of the chain of beacon block headers. 
  #           Sync committees are (i) updated infrequently, and (ii) saved directly in the beacon state, 
  #           allowing light clients to verify the sync committee with a Merkle branch from a 
  #           block header that they already know about, and use the public keys 
  #           in the sync committee to directly authenticate signatures of more recent blocks.
  #   
  #     C. Current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 


  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # ===================================================================
  # STEP 1:  Gather snapshot from node based on finality 
  #           checkpoint and place data into containers
  # ===================================================================
  # ///////////////////////////////////////////////////////////////////

  # ------------------------------------------
  # MAKE API CALLS FOR CHECKPOINT AND SNAPSHOT
  # ------------------------------------------

  #  ==========
  #  CHECKPOINT
  #  ==========
  checkpoint_url = "https://api.allorigins.win/raw?url=https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/states/head/finality_checkpoints" 
  checkpoint = callsAPI(checkpoint_url)
  finalized_checkpoint_root = checkpoint['data']['finalized']['root']  
  
  #  =========
  #  SNAPSHOT
  #  =========
  snapshot_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/snapshot/0xe7ec5a97896da6166bb56b89f9fcb426e13b620b1587dbedda258fd4faa00ab5" 
  snapshot = callsAPI(snapshot_url)
  
  #  Block Header Data
  header_slot =
  header_proposer_index =
  header_parent_root =
  header_state_root = snapshot['data']['header']['state_root']
  header_body_root =
  
  #  Sync Committee Data
  list_of_keys = snapshot['data']['current_sync_committee']['pubkeys']
  hex_aggregate_pubkey = snapshot['data']['current_sync_committee']['aggregate_pubkey']
  current_sync_committee_branch = snapshot['data']['current_sync_committee_branch']


  # ---------------------------------------------------------
  # PARSE JSON INFORMATION ON BLOCK_HEADER AND SYNC_COMMITTEE
  # ---------------------------------------------------------

  #       Aggregate Key and Header State Root
  current_aggregate_pubkey = parseHexToByte(hex_aggregate_pubkey)
  header_state_root = parseHexToByte(header_state_root)
  
  #       List of Keys 
  for i in range(len(list_of_keys)):
    list_of_keys[i] = parseHexToByte(list_of_keys[i])
  
  #       Sync Committee Branch 
  for i in range(len(current_sync_committee_branch)):
    current_sync_committee_branch[i] = parseHexToByte(current_sync_committee_branch[i])

  # ----------------------------------------------
  # CREATE BLOCK_HEADER AND SYNC COMMITTEE OBJECTS
  # ----------------------------------------------
  current_block_header =  BeaconBlockHeader(
    slot = header_slot, 
    proposer_index = header_proposer_index, 
    parent_root = header_parent_root,
    state_root = header_state_root,
    body_root = header_body_root
  )

  current_sync_committee = SyncCommittee(
    pubkeys = list_of_keys,
    aggregate_pubkey = current_aggregate_pubkey
  )



  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # =================================================
  # STEP 2: Verify Merkle branch from sync committee
  # =================================================
  # /////////////////////////////////////////////////

  # -----------------------------------------------------
  #                MERKLEIZE THE OBJECTS
  #
  # Converts the sync committee object into a merkle root
  # -----------------------------------------------------


  sync_committee_root = View.hash_tree_root(current_sync_committee) 

  # -----------------------------------
  # HASH NODE AGAINST THE MERKLE BRANCH
  # -----------------------------------

  # 54 in binary, flipped around 
  index = 54
  path = '011011' 
  
  # Compare hashed answer to the BEACON BLOCK STATE ROOT that the sync committee is a part of!
  assert checkMerkleProof(sync_committee_root, current_sync_committee_branch, path) == header_state_root
  
  
  #                                  \\\\\\\\\\\\\\\\\\\   |||   ////////////////////
  #                                   \\\\\\\\\\\\\\\\\\\   |   ////////////////////
  #                                   ==============================================
  #                                   GET COMMITTEE UPDATES UP UNTIL CURRENT PERIOD:
  #                                   ==============================================
  #                                   ///////////////////   |   \\\\\\\\\\\\\\\\\\\\
  #                                  ///////////////////   |||   \\\\\\\\\\\\\\\\\\\\


  # "The light client stores the snapshot and fetches committee updates until it reaches the latest sync period."

  # What sync periods do I need to get committee_updates for? 
  
  #              |
  #              V
  # From current sync period to latest sync period




  # Fill in these containers and see if the information matches up where it should 
  
  # //////////////////////////
  # ==========================
  # UNDERSTANDING THE SNAPSHOT
  # ==========================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\


  #           PROBLEM:
  # Do I need to hash the beacon block header container together and compare that to the checkpoint root?  
  # I think I do.  This way I'm not blindly trusting that the state root given to me is legitimate 

  # Don't worry about verifying the block header to the checkpoint root right now.
  # Implement that after understanding the committee_update



  # Snapshot gives you... 
  # 
  #     Beacon Block header():          corresponding to Checkpoint root (or any block root specified)
  #            slot:
  #            proposer_index:
  #            parent_root:
  #            state_root:                       <------------------------- The god object that every validator must agree on
  #            body_root:
  #         
  #     SyncCommittee():   
  #            current_sync_committee:  pubkeys[]
  #            aggregate_pubkey:
  
  #     *Additional information given*           <---------- Allows you to verify that the sync committee given is legitimate 
  #            current_sync_committee_branch:
  #
  #  Hashing the merkleized current_sync_committee root against the current_sync_committee_branch and
  #  comparing this to the given state root verifies that the current sync committee is legitamite.  
  # 
  #                               Why is the sync committee so important? 



  # /////////////////////////////////////////////////////////////
  # =============================================================
  # Compare values between the snapshot and the committee updates             (Make pretty program comparing bytes in containers later)
  # =============================================================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  # 
  #
  #                                                            Merkleizing this beacon block header (should) give you the finalized block root. 
  #                                                            Finalized block root --->    root: 0xe7ec5a97896da6166bb56b89f9fcb426e13b620b1587dbedda258fd4faa00ab5  
  #                                                                                         epoch: 127819 
  # 
  #
  #                                                   ============
  #                                                   PERIOD:  499                         <----  snapshot_sync_period = 4090208 // 8192         
  #                                                   ============
  # Snapshot Beacon Block header:                                
  #            slot: 4090208                                                                        
  #            proposer_index: 169657
  #            parent_root: 0x9509dd922c5627b4580f32ae4fbdff01b987b84be1b217d9fce5106dd1b02bb5
  #            state_root: 0xf4f0a5782f3cac46abc52441e32e960e31307a3144120223d83833c110ef5aa5                
  #            body_root:  0x55e7dc7935d59e3e0aeb61fd8957f33d6f0f63e0027af5322778f55bb277a04c
  #         
  #     SyncCommittee():   
  #            current_sync_committee:  pubkeys[]
  #            aggregate_pubkey: 0xb48a95f1b812e42065686ed2ea1a9c094c7aa697d82914294c12c53b5b2c9a53ef8b86d2a8b95b139ca72f8e37741d8f
  # 
  #            current_sync_committee_branch': ['0x0ba8314228d581dff1a3c6dd3cfb56613127ffd33953bfdb9bd7aac80aa283b0', 
  #                                             '0xd771018516266d2dfe5a497468c30bd147e444315a8fc2717c0bf73e66416794', 
  #                                             '0x843daed3ecbb35a0d6ec7cd388ea2a3bd286817aafa273f30213a8091c77bd02', 
  #                                             '0xc78009fdf07fc56a11f122370658a353aaa542ed63e44c4bc15ff4cd105ab33c', 
  #                                             '0xd03297844f949c061d54184b78608b07a0ef6c3d44966a9848c8d3e9f8862174']




  # Difference between snapshot and 
  # committee update attested block header:                             
  # 4090208 - 4088549  = 1659                             ...Feels arbitrary





  # I believe "from" serves last information from a specified period
  # while "to" serves the first information from a specified period.



  #                                                   ============
  #                                                   PERIOD:  499                         <----           attested_header_committee_update = 4088549 // 8192
  #                                                   ============
  #     Committee Update Attested Block header():                 
  #            slot: 4088549
  #            proposer_index:  363243
  #            parent_root:  0x25feb7de799df84b9a322a30363140f484f5d71c67657cebbeaa672b762fd0b8
  #            state_root:  0x12ee41d13b6331070297163a9348c4248e620c0f72a4c14d63e60826bad2d492
  #            body_root:  0x89a724e8ead4f0058f2f543e19469e4340ee5cbd9cf1ad480f9d448d23dfecff
  #
  #     SyncCommittee():   
  #            next_sync_committee: pubkeys[]
  #            aggregate_pubkey:   0x8f56f5731e74702f20c29240f4706662cfbc3e003359592a792c68704700d4cf4b63eb76b1e571cefd8aaec3f0ccf972
  #     next_sync_committee_branch:  ['0x152456a0396e4e57f4d93b3d746e5295faaa744d6426772bd185427499e65f68', 
  #                                   '0xe86e77b209c622ba5cf73e5dc147fe4064cc869022aa750b4bc13b564824ffc2', 
  #                                   '0x1f64c0c5cf6e8bb403bb55085b03903ce4054fbbe7b51ea6c929e2c53432f357', 
  #                                   '0xc78009fdf07fc56a11f122370658a353aaa542ed63e44c4bc15ff4cd105ab33c', 
  #                                   '0x717da9e060636db4d7827af544116e805325a9fe84ee69b278b8e89c45701ef6']
  #
  #
  #     Finalized Block header():                   ~ Same period ~ 
  #            slot: 4088480
  #            proposer_index:  280599
  #            parent_root:  0xee77ad7b118621652d887107acf4ce75004d41c490218a5ce3af4dc048ed4eca
  #            state_root:   0x59531ed8dc5cc5a09c2b4942df3a8f64d90e911938ff4b0497fbc054f6cd2383
  #            body_root:   0x14157a187a5f89f0b4d053eb411dd6d786f2123a677043742d1aa2ab6717910f
  # 
  #     finality_branch:              ['0x15f3010000000000000000000000000000000000000000000000000000000000', 
  #                                    '0x9ce6b6b3c47bd19f386dc0e069466d6a5b545c933bd02a6105558c37d032156d', 
  #                                    '0x735bbf79e46e392630d98b2f7dc93ca23e9067d8bd689eeabb0cf9c498c59960', 
  #                                    '0xd7ee1b5499dbe7a3d120917a75386dea0dd5c09feff600019aba9b6da8fbf9bf',
  #                                    '0xc78009fdf07fc56a11f122370658a353aaa542ed63e44c4bc15ff4cd105ab33c',
  #                                    '0x60810812caba398c56e244608ec5b2c354da8949ed85f4d353f74bd628e7ec07']
  #
  #     sync_aggregate:
  #            sync_committee_bits:  0xffffffffffffffffffffdfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
  #            sync_committee_signature:  0xabdc4eeede5ae7ccb4b2c274dc3880c4c532bc85009726c042c3958f231ee212e8a215c39e3500b969f7a78af512aada05302a528cd9cf467dca64c0225907a315d30ceffa476a8976f5422e02954c4267f547a989a2c0251358ec4a514a8a6b
  #     fork_version: 0x01000000         
  #
  
  
  #                                                   ============
  #                                                   PERIOD:  500                          <----           attested_header_committee_update = 4096341 // 8192
  #                                                   ============
  #     Attested Block header():          
  #            slot:  4096341
  #            proposer_index:  232694
  #            parent_root:  0xd79c776e8a397662caa120ebc551a7386f6a6c3b9c1d9701e0445ca723960ada
  #            state_root:  0x4e0a3e83021bee33b74f22799e3950941cef48d01a8c80cd277ad8ad155db12f                     
  #            body_root:  0x09c2005b4737a29d933e9b59d8c3f8fd3fbdbef6a07abbe2b6a3cb58c77dd931
  #
  #     SyncCommittee():   
  #            next_sync_committee: pubkeys[]
  #            aggregate_pubkey:  0x97e29f45b379816b7bd6d132975be014b01128bc8349e4e24018618bcd0a17e3bc1844f05eb5f52f7d7a1eba91705e93
  #  
  #     next_sync_committee_branch:   ['0x0ba8314228d581dff1a3c6dd3cfb56613127ffd33953bfdb9bd7aac80aa283b0',
  #                                    '0x36a7ef9ed083ebcb6c5056e8db15901e062c2889ae93cb156c1d015f8145c231', 
  #                                    '0x227a14c446a5789da5bd8ad0f769f04e5a2789fbd2201e1187d4e3b2ad8b86e1', 
  #                                    '0xc78009fdf07fc56a11f122370658a353aaa542ed63e44c4bc15ff4cd105ab33c', 
  #                                    '0x28b2aacd237776b49d039508a49b833486ab9bcc57c8cab45ce7d6c25975cf70']
  #
  #     Finalized Block header():                    
  #            slot:  4096256
  #            proposer_index:  347342
  #            parent_root:  0x6b7872e0208b5884f3a26a45e67d52043548fc631835913b126fd8e7d1f07485
  #            state_root:  0xf8f063d1927e9ca28afc39c03ca18b5d83c13acd841c7e1c49d4e4b36a0d5f3a
  #            body_root:  0x8c7e9298dd0facb26dcd6149e8add152ea088b07dad083414ac6e920f4cd331a
  # 
  #     finality_branch:  ['0x08f4010000000000000000000000000000000000000000000000000000000000',
  #                        '0x970a49db40b2da18f9ff2f7a687288f623a0d5d425f92e22ef12a8c41177c505', 
  #                        '0x851f7972d98854453c3fc72082be68d727e4eba0f9d56bb17a9023c1d67e8037', 
  #                        '0x71eff478cc51e973c7114c0264f37258b7645aa448745dc9273cb94273f5b6ac',
  #                        '0xc78009fdf07fc56a11f122370658a353aaa542ed63e44c4bc15ff4cd105ab33c', 
  #                        '0xbe5ff7265537bd15a499312ea447e8419aa7fd31972e2ca976c81712266cea9e']
  #
  #     sync_aggregate:
  #            sync_committee_bits:   0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
  #            sync_committee_signature:   0xa3d6cf7750cf7904990cac72e8075446febd080b06922099590d2abe8930c68a57513e6b1582390931ac122ef801de340f71d65d3eeb196358af052527a14e81be711512acd704833699486e18cc50feb589fe75652aaf0925037331b7116683
  #     fork_version:  0x01000000        
















  # //////////////////////////////////
  # ==================================
  # UNDERSTANDING THE COMMITTEE_UPDATE
  # ==================================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
  committee_updates_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/lightclient/committee_updates?from=499&to=500" 
  committee_updates = callsAPI(committee_updates_url)
  print("\n") 
  print("Committee_updates: ") 
  print(committee_updates)
   
  # Committee update gives you...
  # 
  #     Attested Block header():          for sync period
  #            slot:
  #            proposer_index:
  #            parent_root:
  #            state_root:                       <------------------------- The god object that every validator must agree on
  #            body_root:
  #
  #     SyncCommittee():   
  #            next_sync_committee: pubkeys[]
  #            aggregate_pubkey:
  #  
  #     next_sync_committee_branch:
  #
  #
  #     ** FIND OUT WHERE THIS DATA STRUCTURE LIES **
  #
  #
  #     Finalized Block header():                    <---- This might not be the correct label.  Figure out what I'm looking at!
  #            slot:
  #            proposer_index:
  #            parent_root:
  #            state_root:
  #            body_root:
  # 
  #     finality_branch:
  #
  #     sync_aggregate:
  #            sync_committee_bits:
  #            sync_committee_signature:
  #     fork_version:          
  #
  #
  # 
  #  
  # ... for each period you want:   from -> to 
  
  # print(committee_updates)
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  # Compare the merkleized next_sync committee to the state root from the snapshot
  



  # # This only gives current sync committee
  # # Call the snapshot of the next beacon state given in checkpoint 



  # # What periods do I sync from?
  
  # committee_updates_slot_number = int(committee_updates['data'][0]['attested_header']['slot'])
  
  
  
  # # Is committee updates information one sync period ahead of current period?
  # # Why is the slot difference negative?
  # slot_difference =  committee_updates_slot_number - snapshot_slot_number
  # print("Slot difference: " + str(slot_difference)) 
  
 
  # # if slot_difference <= 8192 & slot_difference > 0:
  # #   print("Probably next slot.")               #  I still dont know if the checkpoint is the final block of a period or the first block of the next     

  
  # print('Snapshot state root: ' + str()) 
  # committee_updates_parent_root = committee_updates['data'][0]['attested_header']['parent_root']
  # print("Committee update parent root: " + str(committee_updates_parent_root)) 

  
  # # # Call lightclient/committee_updates to get committee updates from that period to the current period
  # # next_sync_committee = SyncCommittee(
  # #   pubkeys = next_list_keys,
  # #   aggregate_pubkey = next_aggregate_pubkey
  # # )

  # # next_sync_committee_root = View.hash_tree_root(next_sync_committee) 

  # # 55 in binary, flipped around 
  # next_index = 55
  # next_path = "111011"

  # # checkMerkleProof(next_sync_committee_root, next_sync_branch, next_path)







  # Figure out what all I need to store in the LightClientStore Container
  # Do I need to have light client store container initialized first? 



  #                                   \\\\\\\\\\\\\\\\\\\ || ////////////////////
  #                                    \\\\\\\\\\\\\\\\\\\  ////////////////////
  #                                    ========================================
  #                                    SYNC TO THE LATEST FINALIZED CHECKPOINT:
  #                                    ========================================
  #                                    ///////////////////  \\\\\\\\\\\\\\\\\\\\
  #                                   /////////////////// || \\\\\\\\\\\\\\\\\\\\