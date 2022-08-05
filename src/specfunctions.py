from containers import (ALTAIR_FORK_EPOCH,
                        ALTAIR_FORK_VERSION,
                        CURRENT_SYNC_COMMITTEE_INDEX,
                        DOMAIN_SYNC_COMMITTEE,
                        FINALIZED_ROOT_INDEX,
                        GENESIS_FORK_VERSION, 
                        GENESIS_SLOT, 
                        MIN_SYNC_COMMITTEE_PARTICIPANTS, 
                        NEXT_SYNC_COMMITTEE_INDEX, 
                        SLOTS_PER_EPOCH,
                        SLOTS_PER_SYNC_PERIOD,
                        UPDATE_TIMEOUT,
                        Bytes32,
                        Domain, 
                        DomainType,
                        Epoch, 
                        Root, 
                        Slot,
                        SSZObject, 
                        Version,
                        uint64,
                        BeaconBlockHeader,
                        ForkData,
                        LightClientBootstrap,
                        LightClientFinalityUpdate,
                        LightClientOptimisticUpdate,
                        LightClientStore, 
                        LightClientUpdate, 
                        SigningData, 
                        SyncCommittee)
from merkletreelogic import floorlog2, is_valid_merkle_branch
from py_ecc.bls import G2ProofOfPossession
from remerkleable.core import View



def compute_epoch_at_slot(slot_number):
  epoch = slot_number // SLOTS_PER_EPOCH 
  return epoch

def compute_domain(domain_type: DomainType, fork_version: Version=None, genesis_validators_root: Root=None) -> Domain:
    """
    Return the domain for the ``domain_type`` and ``fork_version``.
    """
    if fork_version is None:
        fork_version = GENESIS_FORK_VERSION
    if genesis_validators_root is None:
        genesis_validators_root = Root()  # all bytes zero by default
    fork_data_root = compute_fork_data_root(fork_version, genesis_validators_root)
    return Domain(domain_type + fork_data_root[:28])

def compute_fork_data_root(current_version: Version, genesis_validators_root: Root) -> Root:
    """
    Return the 32-byte fork data root for the ``current_version`` and ``genesis_validators_root``.
    This is used primarily in signature domains to avoid collisions across forks/chains.
    """
    return View.hash_tree_root(ForkData(
        current_version=current_version,
        genesis_validators_root=genesis_validators_root,
    ))

def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= ALTAIR_FORK_EPOCH:
        return ALTAIR_FORK_VERSION
    return GENESIS_FORK_VERSION

def compute_signing_root(ssz_object: SSZObject, domain: Domain) -> Root:
    """
    Return the signing root for the corresponding signing data.
    """
    return View.hash_tree_root(SigningData(
        object_root=View.hash_tree_root(ssz_object),
        domain=domain,
    ))

def compute_sync_committee_period_at_slot(slot_number):
  sync_period = slot_number // SLOTS_PER_SYNC_PERIOD 
  return sync_period

def is_finality_update(update: LightClientUpdate) -> bool:
    return update.finality_branch != [Bytes32() for _ in range(floorlog2(FINALIZED_ROOT_INDEX))]

#   is_better_update                       (update, store.best_valid_update)
def is_better_update(new_update: LightClientUpdate, old_update: LightClientUpdate) -> bool:
    # Compare supermajority (> 2/3) sync committee participation
    max_active_participants = len(new_update.sync_aggregate.sync_committee_bits)
    new_num_active_participants = sum(new_update.sync_aggregate.sync_committee_bits)
    old_num_active_participants = sum(old_update.sync_aggregate.sync_committee_bits)
    new_has_supermajority = new_num_active_participants * 3 >= max_active_participants * 2
    old_has_supermajority = old_num_active_participants * 3 >= max_active_participants * 2
    if new_has_supermajority != old_has_supermajority:
        return new_has_supermajority > old_has_supermajority
    if not new_has_supermajority and new_num_active_participants != old_num_active_participants:
        return new_num_active_participants > old_num_active_participants

    # Compare presence of relevant sync committee
    new_has_relevant_sync_committee = is_sync_committee_update(new_update) and (
        compute_sync_committee_period_at_slot(new_update.attested_header.slot)
        == compute_sync_committee_period_at_slot(new_update.signature_slot)
    )
    old_has_relevant_sync_committee = is_sync_committee_update(old_update) and (
        compute_sync_committee_period_at_slot(old_update.attested_header.slot)
        == compute_sync_committee_period_at_slot(old_update.signature_slot)
    )
    if new_has_relevant_sync_committee != old_has_relevant_sync_committee:
        return new_has_relevant_sync_committee

    # Compare indication of any finality
    new_has_finality = is_finality_update(new_update)
    old_has_finality = is_finality_update(old_update)
    if new_has_finality != old_has_finality:
        return new_has_finality

    # Compare sync committee finality
    if new_has_finality:
        new_has_sync_committee_finality = (
            compute_sync_committee_period_at_slot(new_update.finalized_header.slot)
            == compute_sync_committee_period_at_slot(new_update.attested_header.slot)
        )
        old_has_sync_committee_finality = (
            compute_sync_committee_period_at_slot(old_update.finalized_header.slot)
            == compute_sync_committee_period_at_slot(old_update.attested_header.slot)
        )
        if new_has_sync_committee_finality != old_has_sync_committee_finality:
            return new_has_sync_committee_finality

    # Tiebreaker 1: Sync committee participation beyond supermajority
    if new_num_active_participants != old_num_active_participants:
        return new_num_active_participants > old_num_active_participants

    # Tiebreaker 2: Prefer older data (fewer changes to best)
    if new_update.attested_header.slot != old_update.attested_header.slot:
        return new_update.attested_header.slot < old_update.attested_header.slot
    return new_update.signature_slot < old_update.signature_slot

def is_sync_committee_update(update: LightClientUpdate) -> bool:
    return update.next_sync_committee_branch != [Bytes32() for _ in range(floorlog2(NEXT_SYNC_COMMITTEE_INDEX))]

def get_active_header(update: LightClientUpdate) -> BeaconBlockHeader:
    # The "active header" is the header that the update is trying to convince us
    # to accept. If a finalized header is present, it's the finalized header,
    # otherwise it's the attested header
    if is_finality_update(update):
        return update.finalized_header
    else:
        return update.attested_header

def is_next_sync_committee_known(store: LightClientStore) -> bool:
    return store.next_sync_committee != SyncCommittee()

def get_safety_threshold(store: LightClientStore) -> uint64:
    return max(
        store.previous_max_active_participants,
        store.current_max_active_participants,
    ) // 2



#                                           \~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
#                                            \ =========================== /
#
#                                              Light Client Initialization
#
#                                            / =========================== \
#                                           /~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\

def initialize_light_client_store(trusted_block_root: Root,
                                  bootstrap: LightClientBootstrap) -> LightClientStore:
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



#                                           \~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
#                                            \ ========================== /
#
#                                              Light Client State Updates
#
#                                            / ========================== \
#                                           /~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\

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
#
#  MAP THE LINKS OF THE ROOTS WE USE IN MERKLE PROOFS BACK TO THE TRUSTED CHECKPOINT ROOT!  Create a diagram
def validate_light_client_update(store: LightClientStore,
                                 update: LightClientUpdate,
                                 current_slot: Slot,
                                 genesis_validators_root: Root,
                                 ) -> None:
    print("\n") 
    print("Store's sync period: " + str(compute_sync_committee_period_at_slot(store.finalized_header.slot)))
    print("Update's sync period: " + str(compute_sync_committee_period_at_slot(update.finalized_header.slot)))
    
    # Verify sync committee has sufficient participants
    sync_aggregate = update.sync_aggregate
    assert sum(sync_aggregate.sync_committee_bits) >= MIN_SYNC_COMMITTEE_PARTICIPANTS

    # Verify update does not skip a sync committee period
    assert current_slot >= update.signature_slot > update.attested_header.slot >= update.finalized_header.slot 
    store_period = compute_sync_committee_period_at_slot(store.finalized_header.slot)
    update_signature_period = compute_sync_committee_period_at_slot(update.signature_slot)

    if is_next_sync_committee_known(store):                                          #    Next committee is known when you're past the bootstrap initialization
        assert update_signature_period in (store_period, store_period + 1)                        
    else:
        assert update_signature_period == store_period                         

    # Verify update is relevant
    update_attested_period = compute_sync_committee_period_at_slot(update.attested_header.slot)
    update_has_next_sync_committee = not is_next_sync_committee_known(store) and (                #   <----  I believe this takes care of the bootstrap period messiness 
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
            # depth=floorlog2(FINALIZED_ROOT_INDEX),
            index=FINALIZED_ROOT_INDEX,                                
            root=update.attested_header.state_root,
        )
    #        ^^^ THIS ASSERTION PASSES!

    # ========================================================================================== 
    #  I need to create/use a test suite. Look at Etan's test files.  Look at Clara's test files 
    # ========================================================================================== 

    # Verify that the `next_sync_committee`, if present, actually is the next sync committee saved in the
    # state of the `attested_header`
    if not is_sync_committee_update(update):      
        assert update.next_sync_committee == SyncCommittee()
    else:
        if update_attested_period == store_period and is_next_sync_committee_known(store):
            assert update.next_sync_committee == store.next_sync_committee     
        
        assert is_valid_merkle_branch(
            #  Next sync committee corresponding to 'attested header'
            leaf=View.hash_tree_root(update.next_sync_committee),               
            branch=update.next_sync_committee_branch,                   
            # depth=floorlog2(NEXT_SYNC_COMMITTEE_INDEX),          
            index=NEXT_SYNC_COMMITTEE_INDEX,                        
            root=update.finalized_header.state_root,                                   # spec said "attested_header.state_root"
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

    fork_version = compute_fork_version(compute_epoch_at_slot(update.signature_slot))            
    domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)        
    signing_root = compute_signing_root(update.attested_header, domain)


    #   Muting assertion for now.  Do ya think the assertion might not work
    #   because of something that's wrong in the update.next_sync_committee assertion?
    #   What if I just use the fork version given to me in the update api?
    # 
    #   There are a lot of constants/different pieces of data going into this thing... For instance,
    #   signing_root takes in update's attested_header and domain!  
    #   Is my update.attested_header wrong???  
    #   That might explain why my proof doesn't match my attested_header.state_root! <-----Noooo because 
    #                                                            the update.attested_header.state works in the proof right before it   

    # DATA CHECK
    #    fork_version: Same in constant as it is in function.  PASS
    #    domain:          found the genesis validators root.   PASS
    #    signing root:    If the fork_version and domain are correct, that leaves me with the attested_header.

    assert G2ProofOfPossession.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature)       # spec uses bls.FastAggregateVerify()
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
