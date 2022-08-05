"""  
                                     IMPORTANT QUESTION:

          How do I tie the finalized block header back to the bootstrap checkpoint root?
          Because right now there's a gap in the logic:  
          Yes the next sync committee hashes against merkle proof to equal the finalized state,
          but the finalized state isn't connected back to the checkpoint root.
          print(finalized_block_header_root)
 
                  For now, press on and execute spec functions properly
""" 

# If all goes well, we'll update our light client memory with this header
# The header is the key trusted piece of data we use to verify merkle proofs against.
# From a beacon block, we can use merkle proofs to verify data about everything.  ie beacon state


"""                             
  
      Get block header at slot N in period X = N // 16384
      Ask node for current sync committee + proof of checkpoint root
      Node responds with a snapshot
      
      Snapshot contains:
      A. Header- Block's header corresponding to the checkpoint root
      
            The light client stores a header so it can ask for merkle branches to 
            authenticate transactions and state against the header
  
      B. Current sync committee- Public Keys and the aggregated pub key of the current sync committee
    
            The purpose of the sync committee is to allow light clients to keep track
            of the chain of beacon block headers. 
            Sync committees are (i) updated infrequently, and (ii) saved directly in the beacon state, 
            allowing light clients to verify the sync committee with a Merkle branch from a 
            block header that they already know about, and use the public keys 
            in the sync committee to directly authenticate signatures of more recent blocks.
    
      C. Current sync committee branch- Proof of the current sync committee in the form of a Merkle branch 
"""


"""
                                      \\\\\\\\\\\\\\\\\\\ || ////////////////////
                                       \\\\\\\\\\\\\\\\\\\  ////////////////////
                                       =========================================
                                       INITIALIZATION/BOOTSTRAPPING TO A PERIOD:
                                       =========================================
                                       ///////////////////  \\\\\\\\\\\\\\\\\\\\
                                      /////////////////// || \\\\\\\\\\\\\\\\\\\\
"""


"""
                                   \\\\\\\\\\\\\\\\\\\   |||   ////////////////////
                                    \\\\\\\\\\\\\\\\\\\   |   ////////////////////
                                    ==============================================
                                    GET COMMITTEE UPDATES UP UNTIL CURRENT PERIOD:
                                    ==============================================
                                    ///////////////////   |   \\\\\\\\\\\\\\\\\\\\
                                   ///////////////////   |||   \\\\\\\\\\\\\\\\\\\\

      "The light client stores the snapshot and fetches committee updates until it reaches the latest sync period."
                        Get sycn period updates from current sync period to latest sync period
"""

"""
  A light client maintains its state in a store object of type LightClientStore and receives update objects of type LightClientUpdate. 
  Every update triggers process_light_client_update(store, update, current_slot) where current_slot is the current slot based on some local clock.
"""




""" 
Introduces a new `LightClientBootstrap` structure to allow setting up a
`LightClientStore` with the initial sync committee and block header from
a user-configured trusted block root.

This leads to new cases where the `LightClientStore` is only aware of
the current but not the next sync committee. As a side effect of these
new cases, the store's `finalized_header` may now  advance into the next
sync committee period before a corresponding `LightClientUpdate` with
the new sync committee is obtained, improving responsiveness.

Note that so far, `LightClientUpdate.attested_header.slot` needed to be
newer than `LightClientStore.finalized_header.slot`. However, it is now
necessary to also consider certain older updates to try and backfill the
`next_sync_committee`. The `is_better_update` helper is also updated to
improve `best_valid_update` tracking.

          - Etan Status:    commit 654970c6057011e407299a61610c697662c335bd
"""