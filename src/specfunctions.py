from containers import (CURRENT_SYNC_COMMITTEE_INDEX,
                        DOMAIN_SYNC_COMMITTEE,
                        FINALIZED_ROOT_INDEX,
                        GENESIS_SLOT, 
                        MIN_SYNC_COMMITTEE_PARTICIPANTS, 
                        NEXT_SYNC_COMMITTEE_INDEX, 
                        UPDATE_TIMEOUT,
                        Bytes32,
                        Root, 
                        Slot,
                        BeaconBlockHeader,
                        LightClientBootstrap,
                        LightClientFinalityUpdate,
                        LightClientOptimisticUpdate,
                        LightClientStore, 
                        LightClientUpdate, 
                        SyncCommittee)
from helper import (compute_epoch_at_slot,
                    compute_domain,
                    compute_fork_version,
                    compute_signing_root,
                    compute_sync_committee_period_at_slot,
                    get_safety_threshold,
                    is_better_update,
                    is_finality_update,
                    is_next_sync_committee_known,
                    is_sync_committee_update,
)
from merkletreelogic import floorlog2, is_valid_merkle_branch
from py_ecc.bls import G2ProofOfPossession as py_ecc_bls                       # I believe both of these work
from remerkleable.core import View


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
        # depth=floorlog2(CURRENT_SYNC_COMMITTEE_INDEX),
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
    update_signature_period = compute_sync_committee_period_at_slot(update.signature_slot)
    
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
            index=FINALIZED_ROOT_INDEX,                                
            root=update.attested_header.state_root,
        )
    #        ^^^ THIS ASSERTION PASSES!

    # Verify that the next_sync_committee, if present, actually is the next sync committee saved in the state of the attested_header
    if not is_sync_committee_update(update):      
        assert update.next_sync_committee == SyncCommittee()
    else:
        if update_attested_period == store_period and is_next_sync_committee_known(store):
            assert update.next_sync_committee == store.next_sync_committee     
        
        assert is_valid_merkle_branch(
            #  Next sync committee corresponding to 'attested header'
            leaf=View.hash_tree_root(update.next_sync_committee),               
            branch=update.next_sync_committee_branch,                   
            index=NEXT_SYNC_COMMITTEE_INDEX,                        
            root=update.finalized_header.state_root,                                   
            # root=update.attested_header.state_root,              # <--- spec says this                     
        )
    
    # "The next_sync_committee can no longer be considered finalized based
    # on is_finality_update. Instead, waiting until finalized_header is
    # in the attested_header's sync committee period is now necessary."  - Etan-Status PR #2932  

    # Verify sync committee aggregate signature
    if update_signature_period == store_period:
        sync_committee = store.current_sync_committee
    else:
        sync_committee = store.next_sync_committee
    participant_pubkeys = [                                                                                   
        pubkey for (bit, pubkey) in zip(sync_aggregate.sync_committee_bits, sync_committee.pubkeys)
        if bit
    ]
    # Maybe my update.attested_header is wrong?  Check my pubkeys logic too.   

    fork_version = compute_fork_version(compute_epoch_at_slot(update.attested_header.slot))      # update.signature_slot     
    domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)        
    signing_root = compute_signing_root(update.attested_header, domain)

    assert py_ecc_bls.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature)       
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
        signature_slot=finality_update.signature_slot,
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
        signature_slot=optimistic_update.signature_slot,
    )
    
    process_light_client_update(store, update, current_slot, genesis_validators_root)


#                                           \~~~~~~~~~~~~~~~~~~/
#                                            \ ============== /
#                                               MY FUNCTIONS
#                                            / ============== \
#                                           /~~~~~~~~~~~~~~~~~~\


#  Move lightclient.py functions here when Lodestar's servers are back up.


















# =============================
#  IMPORTANT TEST VALUES BELOW!
# =============================

    # print("\n")
    # print("\n")
    # print("\n")
    # print("\n")
    # print("\n")

    # print("Sync period: " + str(compute_sync_committee_period_at_slot(update.finalized_header.slot)))
    # print("\n")
    # print("Light Client Store: ")
    # print("\n")
    # print("   finalized_header: ")
    # print("        slot: " + str(store.finalized_header.slot))
    # print("        proposer_index: " + str(store.finalized_header.proposer_index))
    # print("        parent_root: " + str(store.finalized_header.parent_root))
    # print("        state_root: " + str(store.finalized_header.state_root))
    # print("        body_root: " + str(store.finalized_header.body_root))
    # print("   current_sync_committee: "  + str(store.current_sync_committee))
    # print("   next_sync_committee: "  + str(store.next_sync_committee))
    # print("   best_valid_update: "+ str(store.best_valid_update))
    # print("   optimistic_header: "+ str(store.optimistic_header))
    # print("   previous_max_active_participants: "+ str(store.previous_max_active_participants))
    # print("   current_max_active_participants: "+ str(store.current_max_active_participants))
    
    # print("\n")
    # print("\n")
    # print("\n")
    # print("\n")
    # print("\n")
    # print("\n")
    # print("Light Client Update: ")
    # print("\n")
    # print("   attested_header: ")
    # print("        slot: " + str(update.attested_header.slot))
    # print("        proposer_index: " + str(update.attested_header.proposer_index))
    # print("        parent_root: " + str(update.attested_header.parent_root))
    # print("        state_root: " + str(update.attested_header.state_root))
    # print("        body_root: " + str(update.attested_header.body_root))
    # print("   next_sync_committee: "  + str(update.next_sync_committee))
    # print("   next_sync_committee branch: " + str(bytes(update.next_sync_committee_branch)))
    # print("   finalized_header: ")
    # print("        slot: " + str(update.finalized_header.slot))
    # print("        proposer_index: " + str(update.finalized_header.proposer_index))
    # print("        parent_root: " + str(update.finalized_header.parent_root))
    # print("        state_root: " + str(update.finalized_header.state_root))
    # print("        body_root: " + str(update.finalized_header.body_root))
    
    # print("   finality_branch: "+ str(bytes(update.finality_branch)))
    # print("   sync_aggregate: "+ str(update.sync_aggregate))
    # print("   signature_slot: "+ str(update.signature_slot))
