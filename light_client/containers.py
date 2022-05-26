from numpy import uint64
# Containers - A Container class can be described as a special component that can hold the gathering of the components.
#              A component is an identifiable part of a larger program or construction. Seperation of concerns

# Define custom types:
Slot = uint64
Epoch = uint64
CommitteeIndex = uint64
ValidatorIndex	= uint64	
Gwei =	uint64	
# How do i turn this data type into something I can use in python?
Root =	Bytes32	
Hash32	= Bytes32
Version	= Bytes4	
DomainType = Bytes4	
ForkDigest = Bytes4	
Domain = Bytes32	
BLSPubkey =	Bytes48
BLSSignature = Bytes96

class BeaconBlockHeader(Container):
    slot: Slot
    parent_root: Root
    state_root: Root
    body_root: Root

class LightClientSnapshot(Container):
    # Beacon block header
    header: BeaconBlockHeader
    # Sync committees corresponding to the header
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee

class LightClientUpdate(Container):
  # The beacon block header that is attested to by the sync committee
  attested_header: BeaconBlockHeader
  # Next sync committee corresponding to the active header
  next_sync_committee: SyncCommittee
  next_sync_committee_branch: Vector[Bytes32, floorlog2(NEXT_SYNC_COMMITTEE_INDEX)]
  # The finalized beacon block header attested to by Merkle branch
  finalized_header: BeaconBlockHeader
  finality_branch: Vector[Bytes32, floorlog2(FINALIZED_ROOT_INDEX)]
  # Sync committee aggregate signature
  sync_aggregate: SyncAggregate
  # Fork version for the aggregate signature
  fork_version: Version

@dataclass
class LightClientStore(object):
  # Beacon block header that is finalized
  finalized_header: BeaconBlockHeader
  # Sync committees corresponding to the header
  current_sync_committee: SyncCommittee
  next_sync_committee: SyncCommittee
  # Best available header to switch finalized head to if we see nothing else
  best_valid_update: Optional[LightClientUpdate]
  # Most recent available reasonably-safe header
  optimistic_header: BeaconBlockHeader
  # Max number of active participants in a sync committee (used to calculate safety threshold)
  previous_max_active_participants: uint64
  current_max_active_participants: uint64