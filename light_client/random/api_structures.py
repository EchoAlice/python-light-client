  # ////////////////////////////
  # ===========================
  # UNDERSTANDING THE BOOTSTRAP
  # ===========================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\

  # Bootstrap gives you... 
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
  
  #           The sync committee is so important because it allows the light client to keep up with the head of the blockchain
  #           efficiently and in real time by only having to check the signature that goes with the head block.  If majority of 
  #           committee signed the block, then you know that is the head of the chain.  Compare all information you want to check
  #           against the beacon state for validity. 
   
  
  # //////////////////////////////////
  # ==================================
  # UNDERSTANDING THE COMMITTEE_UPDATE
  # ==================================
  # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

  # Committee update gives you...
  # 
  #     Attested Block header():         
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
  #
  #     Finalized Block header():                    
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

