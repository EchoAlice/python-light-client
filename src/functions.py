from collections.abc import Sequence
from eth2spec.utils.hash_function import hash
import milagro_bls_binding
from py_ecc.bls import G2ProofOfPossession as py_ecc_bls                       
from remerkleable.core import View
from containers import ( CURRENT_SYNC_COMMITTEE_INDEX,
                         DOMAIN_SYNC_COMMITTEE,
                         FINALIZED_ROOT_INDEX,
                         GENESIS_SLOT, 
                         MIN_GENESIS_TIME,
                         MIN_SYNC_COMMITTEE_PARTICIPANTS, 
                         NEXT_SYNC_COMMITTEE_INDEX, 
                         UPDATE_TIMEOUT,
                         Bytes32,
                         current_time,
                         genesis_validators_root,
                         Root, 
                         Slot,
                         BeaconBlockHeader,
                         LightClientBootstrap,
                         LightClientFinalityUpdate,
                         LightClientOptimisticUpdate,
                         LightClientStore, 
                         LightClientUpdate, 
                         SyncCommittee,
                         time,
                         uint64,
)
from helper import ( current_finality_update_url,
                     current_header_update_url,
                     call_api,
                     compute_epoch_at_slot,
                     compute_domain,
                     compute_fork_version,
                     compute_signing_root,
                     compute_sync_committee_period_at_slot,
                     floorlog2, 
                     get_current_epoch,
                     get_current_slot,
                     get_current_sync_period,
                     get_subtree_index, 
                     get_safety_threshold,
                     hash_pair, 
                     index_to_path, 
                     initialize_light_client_update,
                     initialize_light_client_finality_update, 
                     initialize_light_client_optimistic_update, 
                     is_better_update,
                     is_finality_update,
                     is_next_sync_committee_known,
                     is_sync_committee_update,
                     updates_for_period,
)

#                                           \~~~~~~~~~~~~~~~~~~/
#                                            \ ============== /
#                                              SPEC FUNCTIONS
#                                            / ============== \
#                                           /~~~~~~~~~~~~~~~~~~\

# ===========================
# Light Client Initialization
# ===========================

def initialize_light_client_store(trusted_block_root: Root, bootstrap: LightClientBootstrap) -> LightClientStore:
    assert View.hash_tree_root(bootstrap.header) == trusted_block_root

    assert is_valid_merkle_branch(
        leaf=View.hash_tree_root(bootstrap.current_sync_committee),
        branch=bootstrap.current_sync_committee_branch,
        depth=floorlog2(CURRENT_SYNC_COMMITTEE_INDEX),
        index=CURRENT_SYNC_COMMITTEE_INDEX,
        root=bootstrap.header.state_root,
    )
    return LightClientStore(
        finalized_header=bootstrap.header,
        current_sync_committee=bootstrap.current_sync_committee,
        next_sync_committee=SyncCommittee(),
        best_valid_update=None,
        optimistic_header=bootstrap.header,
        previous_max_active_participants=0,
        current_max_active_participants=0,
    )


# ====================
# Light Client Updates
# ====================

def process_slot_for_light_client_store(store: LightClientStore, current_slot: Slot) -> None:
    # This indicates a shift from one sync period to the next 
    if current_slot % UPDATE_TIMEOUT == 0:
        store.previous_max_active_participants = store.current_max_active_participants
        store.current_max_active_participants = 0
    #  if the current slot is past the store's sync period AND the store has a best valid update
    if (
        current_slot > store.finalized_header.slot + UPDATE_TIMEOUT                               
        and store.best_valid_update is not None
    ):
        # Forced best update when the update timeout has elapsed.
        # Because the apply logic waits for `finalized_header.slot` to indicate sync committee finality,
        # the `attested_header` may be treated as `finalized_header` in extended periods of non-finality
        # to guarantee progression into later sync committee periods according to `is_better_update`.
        if store.best_valid_update.finalized_header.slot <= store.finalized_header.slot:
            store.best_valid_update.finalized_header = store.best_valid_update.attested_header
        apply_light_client_update(store, store.best_valid_update)
        store.best_valid_update = None


#  Look at the currentquestions.py file
def validate_light_client_update(store: LightClientStore,
                                 update: LightClientUpdate,
                                 current_slot: Slot,
                                 genesis_validators_root: Root,
                                 ) -> None:
    
    # Verify sync committee has sufficient participants
    sync_aggregate = update.sync_aggregate
    assert sum(sync_aggregate.sync_committee_bits) >= MIN_SYNC_COMMITTEE_PARTICIPANTS

    # Verify update does not skip a sync committee period
    assert current_slot > update.attested_header.slot >= update.finalized_header.slot 
    store_period = compute_sync_committee_period_at_slot(store.finalized_header.slot)
    update_signature_period = compute_sync_committee_period_at_slot(update.attested_header.slot)          # update.signature_slot 
    
    print("\n") 
    print("Store's sync period: " + str(store_period))
    print("Update's sync period: " + str(update_signature_period))
    # Next committee is known when you're past the bootstrap initialization
    if is_next_sync_committee_known(store):                                          
        assert update_signature_period in (store_period, store_period + 1)                        
    else:
        assert update_signature_period == store_period                         

    # Verify update is relevant
    update_attested_period = compute_sync_committee_period_at_slot(update.attested_header.slot)
    # This takes care of the bootstrap period messiness
    update_has_next_sync_committee = not is_next_sync_committee_known(store) and (                 
        is_sync_committee_update(update) and update_attested_period == store_period                
    )                                                                                                      
    assert (
        update.attested_header.slot > store.finalized_header.slot                                 
        or update_has_next_sync_committee
    )
    

    # Verify that the `finality_branch`, if present, confirms `finalized_header`
    # to match the finalized checkpoint root saved in the state of `attested_header`.
    # Note that the genesis finalized checkpoint root is represented as a zero hash.
    if not is_finality_update(update):
        assert update.finalized_header == BeaconBlockHeader()
    else:
        if update.finalized_header.slot == GENESIS_SLOT:
            finalized_root = Bytes32()
            assert update.finalized_header == BeaconBlockHeader()
        else:
            finalized_root = View.hash_tree_root(update.finalized_header) 
        assert is_valid_merkle_branch(
            leaf=finalized_root,
            branch=update.finality_branch,
            depth=floorlog2(FINALIZED_ROOT_INDEX),
            index=get_subtree_index(FINALIZED_ROOT_INDEX), 
            # index=FINALIZED_ROOT_INDEX,                                
            root=update.attested_header.state_root,
        )
    #        ^^^ THIS ASSERTION PASSES!

    # Verify that the next_sync_committee, if present, actually is the next sync committee saved in the state of the attested_header
    if not is_sync_committee_update(update):      
        assert update.next_sync_committee == SyncCommittee()
    else:
        if update_attested_period == store_period and is_next_sync_committee_known(store):
            assert update.next_sync_committee == store.next_sync_committee     
        # else: 
        #     next_sync_committee_root = View.hash_tree_root(update.next_sync_committee) 
        assert is_valid_merkle_branch(
            #  Next sync committee corresponding to 'attested header'
            # leaf=next_sync_committee_root,               
            leaf=View.hash_tree_root(update.next_sync_committee),               
            branch=update.next_sync_committee_branch,                   
            depth=floorlog2(NEXT_SYNC_COMMITTEE_INDEX), 
            index=get_subtree_index(NEXT_SYNC_COMMITTEE_INDEX),                        
            root=update.finalized_header.state_root,                                   
            # root=update.attested_header.state_root,              # <--- spec says this                     
        )
    # Even after Dade updated logic for proof, my asertion still fails with update's attested_header

    # "The next_sync_committee can no longer be considered finalized based
    # on is_finality_update. Instead, waiting until finalized_header is
    # in the attested_header's sync committee period is now necessary."  - Etan-Status PR #2932  

    # Verify sync committee aggregate signature
    if update_signature_period == store_period:
        sync_committee = store.current_sync_committee
    else:
        sync_committee = store.next_sync_committee
    participant_pubkeys = [                                                                                   
        bytes(pubkey) for (bit, pubkey) in zip(sync_aggregate.sync_committee_bits, sync_committee.pubkeys)
        if bit
    ]

    fork_version = compute_fork_version(compute_epoch_at_slot(update.attested_header.slot))           
    domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)        
    signing_root = compute_signing_root(update.attested_header, domain)

    # print('signing_root: '+str(signing_root))
    # print('sync_agg.sync_comm_sig: '+str(type(sync_aggregate.sync_committee_signature)))

    # assert py_ecc_bls.FastAggregateVerify(participant_pubkeys, signing_root, bytes(sync_aggregate.sync_committee_signature))       
    assert milagro_bls_binding.FastAggregateVerify(participant_pubkeys, signing_root, bytes(sync_aggregate.sync_committee_signature))       
    print("Validation successful")


def apply_light_client_update(store: LightClientStore, update: LightClientUpdate) -> None:
    store_period = compute_sync_committee_period_at_slot(store.finalized_header.slot)
    update_finalized_period = compute_sync_committee_period_at_slot(update.finalized_header.slot)
    if not is_next_sync_committee_known(store):
        assert update_finalized_period == store_period
        store.next_sync_committee = update.next_sync_committee
    elif update_finalized_period == store_period + 1:
        store.current_sync_committee = store.next_sync_committee
        store.next_sync_committee = update.next_sync_committee
    if update.finalized_header.slot > store.finalized_header.slot:
        store.finalized_header = update.finalized_header
        if store.finalized_header.slot > store.optimistic_header.slot:
            store.optimistic_header = store.finalized_header

def process_light_client_update(store: LightClientStore,
                                update: LightClientUpdate,
                                current_slot: Slot,
                                genesis_validators_root: Root,) -> None:
    validate_light_client_update(store, update, current_slot, genesis_validators_root)

    sync_committee_bits = update.sync_aggregate.sync_committee_bits
    # Update the best update in case we have to force-update to it if the timeout elapses
    if (
        store.best_valid_update is None
        or is_better_update(update, store.best_valid_update)
    ):
        store.best_valid_update = update

    # Track the maximum number of active participants in the committee signatures
    store.current_max_active_participants = max(
        store.current_max_active_participants,
        sum(sync_committee_bits),
    )

    # Update the optimistic header
    if (
        sum(sync_committee_bits) > get_safety_threshold(store)
        and update.attested_header.slot > store.optimistic_header.slot
    ):
        store.optimistic_header = update.attested_header

    #   Does the light client update get wiped out after it's processed?   
    #   It just changes to the next periods update via sync_to_current_period()
    # 
    # Update finalized header
    update_has_finalized_next_sync_committee = (                                            #  This variable == true when syncing to the current sync period
        not is_next_sync_committee_known(store)
        and is_sync_committee_update(update) and is_finality_update(update) and (
            compute_sync_committee_period_at_slot(update.finalized_header.slot)
            == compute_sync_committee_period_at_slot(update.attested_header.slot)
        )
    )
    if (
        sum(sync_committee_bits) * 3 >= len(sync_committee_bits) * 2 
        and (
            update.finalized_header.slot > store.finalized_header.slot
            or update_has_finalized_next_sync_committee
        )
    ):
        # Normal update through 2/3 threshold
        apply_light_client_update(store, update)
        store.best_valid_update = None

def process_light_client_finality_update(store: LightClientStore,
                                         finality_update: LightClientFinalityUpdate,
                                         current_slot: Slot,
                                         genesis_validators_root: Root) -> None:
    update = LightClientUpdate(
        attested_header=finality_update.attested_header,
        next_sync_committee=SyncCommittee(),
        next_sync_committee_branch=[Bytes32() for _ in range(floorlog2(NEXT_SYNC_COMMITTEE_INDEX))],
        finalized_header=finality_update.finalized_header,
        finality_branch=finality_update.finality_branch,
        sync_aggregate=finality_update.sync_aggregate,
    )
    process_light_client_update(store, update, current_slot, genesis_validators_root)

def process_light_client_optimistic_update(store: LightClientStore,
                                           optimistic_update: LightClientOptimisticUpdate,
                                           current_slot: Slot,
                                           genesis_validators_root: Root) -> None:
    update = LightClientUpdate(
        attested_header=optimistic_update.attested_header,
        next_sync_committee=SyncCommittee(),
        next_sync_committee_branch=[Bytes32() for _ in range(floorlog2(NEXT_SYNC_COMMITTEE_INDEX))],
        finalized_header=BeaconBlockHeader(),
        finality_branch=[Bytes32() for _ in range(floorlog2(FINALIZED_ROOT_INDEX))],
        sync_aggregate=optimistic_update.sync_aggregate,
    )
    
    process_light_client_update(store, update, current_slot, genesis_validators_root)



#                                           \~~~~~~~~~~~~~~~~~~/
#                                            \ ============== /
#                                               MY FUNCTIONS
#                                            / ============== \
#                                           /~~~~~~~~~~~~~~~~~~\

# ====================
# Sync Data Structures
# ====================
# def sync_to_current_period(light_client_store) -> int:
#   sync_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot)
  
#   while True:
#     current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
#     updates = updates_for_period(sync_period)

#     # Status code doesn't equal 200 when there are no more updates, but I should keep track of the current period on my own clock 
#     if updates.status_code == 200:
#       light_client_update = initialize_light_client_update(updates.json())
#       process_light_client_update(light_client_store, 
#                                   light_client_update, 
#                                   current_slot,
#                                   genesis_validators_root)                   
#       time.sleep(1)
#       sync_period += 1
#     else:
#       sync_period = sync_period - 1 
#       return light_client_update



def sync_to_current_updates(light_client_store, light_client_update):          
  previous_sync_period = 0 
  previous_epoch = 0
  previous_slot = 0
  while True:
    current_time = uint64(int(time.time()))                           
    current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
    current_epoch = get_current_epoch(current_time, MIN_GENESIS_TIME)
    current_sync_period = get_current_sync_period(current_time, MIN_GENESIS_TIME) 
    updates = updates_for_period(current_sync_period)

    #  Error occurs during the transition of periods:    "Exception: incorrect bitvector input: 1 bits, vector length is: 512"
    if current_sync_period - previous_sync_period == 1:
      light_client_update = initialize_light_client_update(updates.json()) 
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root)                   
    elif current_epoch - previous_epoch == 1:
      current_finality_update_message = call_api(current_finality_update_url).json()
      finality_update = initialize_light_client_finality_update(current_finality_update_message) 
      process_light_client_finality_update(light_client_store, 
                                           finality_update, 
                                           current_slot, 
                                           genesis_validators_root) 

    elif current_slot - previous_slot == 1:
      current_header_update_message = call_api(current_header_update_url).json()                 
      process_slot_for_light_client_store(light_client_store, current_slot)               
      optimistic_update = initialize_light_client_optimistic_update(current_header_update_message)     
      process_light_client_optimistic_update(light_client_store,
                                             optimistic_update,
                                             current_slot,
                                             genesis_validators_root) 


    previous_sync_period = current_sync_period
    previous_epoch = current_epoch 
    previous_slot = current_slot 
    time.sleep(1)
  return


# ==================
# Merkle Proof Logic 
# ==================
# Try Ethereum's MPL:   I'll have to set up proofs with 5th input
# def is_valid_merkle_branch(leaf: Bytes32, branch: Sequence[Bytes32], depth: uint64, index: uint64, root: Root) -> bool:
#     """
#     Check if ``leaf`` at ``index`` verifies against the Merkle ``root`` and ``branch``.
#     """
#     value = leaf
#     for i in range(depth):
#         if index // (2**i) % 2:
#             value = hash(branch[i] + value)
#         else:
#             value = hash(value + branch[i])
#     return value == root

# When does branch go from being a set of bytes to a weird vector
def is_valid_merkle_branch(leaf: Bytes32, branch: Sequence[Bytes32], depth: uint64, index: uint64, root: Root) -> bool:
    """
    Check if ``leaf`` at ``index`` verifies against the Merkle ``root`` and ``branch``.
    """
    value = leaf
    for i in range(depth):
        branch_value = bytes(branch[i])                   # Maybe let Etan know that you can't hash the remerkleable branch[i] against bytes string 
        if index // (2**i) % 2:
            value = hash(branch_value + value)
        else:
            value = hash(value + branch_value)
    return value == root






# # Mine:
# def is_valid_merkle_branch(leaf, branch, index, root):
#   node_to_hash = leaf
#   hashed_node = 0
#   path = index_to_path(index)
#   branch_index = 0 
#   # TRAVERSE THE PATH BACKWARDS!
#   for i in range(len(branch), 0, -1):                     
#   # Converts vector[Bytes32] (form of branch in container) to a string of bytes (form my function can manipulate)
#     branch_value = bytes(branch[branch_index])                         
#     if path[i] == '0':
#       hashed_node = hash_pair(node_to_hash, branch_value)
#     if path[i] == '1':
#       hashed_node = hash_pair(branch_value, node_to_hash)
#     if(i == 1):                                
#       if hashed_node == root: 
#         return True
#       else: 
#         return False
#     node_to_hash = hashed_node
#     branch_index += 1