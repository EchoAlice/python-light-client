from dataclasses import dataclass
from remerkleable.basic import uint64, byte
from remerkleable.complex import Container, Vector

# Alliases:  (Helps readability of code)
Bytes4 = Vector[byte, 4]
Bytes32 = Vector[byte, 32]
Bytes48 = Vector[byte, 48]
Bytes96 = Vector[byte, 96]

# Define custom types (aka alliases):
Slot = uint64
Epoch = uint64
CommitteeIndex = uint64
ValidatorIndex	= uint64	
Gwei =	uint64	
Root = Bytes32	
Hash32	= Bytes32
Version	= Bytes4
BLSPubkey =	Bytes48
BLSSignature = Bytes96

# Constants:
SYNC_COMMITTEE_SIZE = 512

# Generalized indices for finalized checkpoint and next sync committee in a BeaconState.
# A Generalized index is a way of referring to a poisition of an object in a merkle tree,
# so that the Merkle proof verification algorithm knows what path to check the hashes against
#
# FINALIZED_ROOT_INDEX = get_generalized_index(BeaconState, 'finalized_checkpoint', 'root')
# NEXT_SYNC_COMMITTEE_INDEX = get_generalized_index(BeaconState, 'next_sync_committee')

# Containers - A Container class can be described as a special component that can hold the gathering of the components.

# If all goes well, we'll update our light client memory with this header
# The header is the key trusted piece of data we use to verify merkle proofs against.
# From a beacon block, we can use merkle proofs to verify data about everything.  ie beacon state

class BeaconBlockHeader(Container):
  slot: Slot
  proposer_index: ValidatorIndex
  parent_root: Root
  state_root: Root
  body_root: Root

class SyncCommittee(Container):
  pubkeys: Vector[BLSPubkey, SYNC_COMMITTEE_SIZE]
  aggregate_pubkey: BLSPubkey

# # This is the data we request to stay synced.  We need an update every 27(ish) hours
# class LightClientUpdate(Container):
#   # The beacon block header that is attested to by the sync committee
#   attested_header: BeaconBlockHeader
#   # Next sync committee corresponding to the active header
#   # The committee branch is a merkle proof that we run against the header
#   next_sync_committee: SyncCommittee
#   next_sync_committee_branch: Vector[Bytes32, floorlog2(NEXT_SYNC_COMMITTEE_INDEX)]
#   # The finalized beacon block header attested to by Merkle branch
#   # The header branch is a merkle proof that we run agains the shard block root
#   finalized_header: BeaconBlockHeader
#   finality_branch: Vector[Bytes32, floorlog2(FINALIZED_ROOT_INDEX)]
#   # Sync committee aggregate signature
#   sync_aggregate: SyncAggregate
#   # Fork version for the aggregate signature.  This lets us make sure the votes are for the fork we think we're on
#   fork_version: Version

# @dataclass
# class LightClientStore(object):
#   # Beacon block header that is finalized (not expected to revert)
#   finalized_header: BeaconBlockHeader
#   # Sync committees corresponding to the header
#   current_sync_committee: SyncCommittee
#   next_sync_committee: SyncCommittee
#   # Best available header to switch finalized head to if we see nothing else
#   best_valid_update: Optional[LightClientUpdate]
#   # Most recent available reasonably-safe header
#   optimistic_header: BeaconBlockHeader
#   # Max number of active participants in a sync committee (used to calculate safety threshold)
#   previous_max_active_participants: uint64
#   current_max_active_participants: uint64