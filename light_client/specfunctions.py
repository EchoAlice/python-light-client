from constants import FINALIZED_ROOT_INDEX
from containers import Bytes32, Root, Slot, BeaconBlockHeader, LightClientStore, LightClientUpdate
from math import floor, log2

# should this be an int? or a uint__
def floorlog2(x) -> int:
  return floor(log2(x))

def is_finality_update(update: LightClientUpdate) -> bool:
    return update.finality_branch != [Bytes32() for _ in range(floorlog2(FINALIZED_ROOT_INDEX))]

def get_active_header(update: LightClientUpdate) -> BeaconBlockHeader:
    # The "active header" is the header that the update is trying to convince us
    # to accept. If a finalized header is present, it's the finalized header,
    # otherwise it's the attested header
    if is_finality_update(update):
        return update.finalized_header
    else:
        return update.attested_header

def validate_light_client_update(store: LightClientStore,
                                 update: LightClientUpdate,
                                 current_slot: Slot,
                                 genesis_validators_root: Root) -> None:
    # Verify update slot is larger than slot of current best finalized header
    active_header = get_active_header(update)
    assert current_slot >= update.signature_slot > active_header.slot > store.finalized_header.slot




    # # Verify update does not skip a sync committee period
    # finalized_period = compute_sync_committee_period(compute_epoch_at_slot(store.finalized_header.slot))
    # update_period = compute_sync_committee_period(compute_epoch_at_slot(active_header.slot))
    # signature_period = compute_sync_committee_period(compute_epoch_at_slot(update.signature_slot))
    # assert signature_period in (finalized_period, finalized_period + 1)

    # # Verify that the `finality_branch`, if present, confirms `finalized_header`
    # # to match the finalized checkpoint root saved in the state of `attested_header`.
    # # Note that the genesis finalized checkpoint root is represented as a zero hash.
    # if not is_finality_update(update):
    #     assert update.finalized_header == BeaconBlockHeader()
    # else:
    #     if update.finalized_header.slot == GENESIS_SLOT:
    #         finalized_root = Bytes32()
    #         assert update.finalized_header == BeaconBlockHeader()
    #     else:
    #         finalized_root = hash_tree_root(update.finalized_header)
    #     assert is_valid_merkle_branch(
    #         leaf=finalized_root,
    #         branch=update.finality_branch,
    #         depth=floorlog2(FINALIZED_ROOT_INDEX),
    #         index=get_subtree_index(FINALIZED_ROOT_INDEX),
    #         root=update.attested_header.state_root,
    #     )

    # # Verify that the `next_sync_committee`, if present, actually is the next sync committee saved in the
    # # state of the `active_header`
    # if not is_sync_committee_update(update):
    #     assert update_period == finalized_period
    #     assert update.next_sync_committee == SyncCommittee()
    # else:
    #     if update_period == finalized_period:
    #         assert update.next_sync_committee == store.next_sync_committee
    #     assert is_valid_merkle_branch(
    #         leaf=hash_tree_root(update.next_sync_committee),
    #         branch=update.next_sync_committee_branch,
    #         depth=floorlog2(NEXT_SYNC_COMMITTEE_INDEX),
    #         index=get_subtree_index(NEXT_SYNC_COMMITTEE_INDEX),
    #         root=active_header.state_root,
    #     )

    # sync_aggregate = update.sync_aggregate

    # # Verify sync committee has sufficient participants
    # assert sum(sync_aggregate.sync_committee_bits) >= MIN_SYNC_COMMITTEE_PARTICIPANTS

    # # Verify sync committee aggregate signature
    # if signature_period == finalized_period:
    #     sync_committee = store.current_sync_committee
    # else:
    #     sync_committee = store.next_sync_committee
    # participant_pubkeys = [
    #     pubkey for (bit, pubkey) in zip(sync_aggregate.sync_committee_bits, sync_committee.pubkeys)
    #     if bit
    # ]
    # fork_version = compute_fork_version(compute_epoch_at_slot(update.signature_slot))
    # domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)
    # signing_root = compute_signing_root(update.attested_header, domain)
    # assert bls.FastAggregateVerify(participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature)