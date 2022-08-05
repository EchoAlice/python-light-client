from dataclasses import dataclass
from merkletreelogic import floorlog2
from remerkleable.basic import uint64, byte
from remerkleable.bitfields import Bitvector
from remerkleable.complex import Container, Vector
from typing import Optional
import time

# Alliases:  (Helps readability of code)
Bytes4 = Vector[byte, 4]
Bytes32 = Vector[byte, 32]
Bytes48 = Vector[byte, 48]
Bytes96 = Vector[byte, 96]

# Data type.      Maybe this should be a Vector? idk
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
DomainType = Bytes4
Domain = Bytes32
SSZObject = Container                                                    #  Is this correct?
genesis_validators_root = b'K6=\xb9N(a \xd7n\xb9\x054\x0f\xddNT\xbf\xe9\xf0k\xf3?\xf6\xcfZ\xd2\x7fQ\x1b\xfe\x95' 

# Constants
ALTAIR_FORK_EPOCH =	Epoch(74240)
ALTAIR_FORK_VERSION =	Version('0x01000000')
DOMAIN_SYNC_COMMITTEE = DomainType('0x07000000') 
EPOCHS_PER_SYNC_COMMITTEE_PERIOD = 256      #   2**8
GENESIS_FORK_VERSION = Version('0x00000000') 
GENESIS_SLOT = Slot(0)
MIN_GENESIS_TIME = uint64(1606824000)
MIN_SYNC_COMMITTEE_PARTICIPANTS = 1
CURRENT_SYNC_COMMITTEE_INDEX = 54
NEXT_SYNC_COMMITTEE_INDEX = 55
FINALIZED_ROOT_INDEX = 105   
SECONDS_PER_SLOT = 12
SLOTS_PER_EPOCH = 32                        #   2**5 
SYNC_COMMITTEE_SIZE = 512
SLOTS_PER_SYNC_PERIOD = SLOTS_PER_EPOCH * EPOCHS_PER_SYNC_COMMITTEE_PERIOD
UPDATE_TIMEOUT = SLOTS_PER_SYNC_PERIOD 


# Generalized indices for finalized checkpoint and next sync committee in a BeaconState.
# A Generalized index is a way of referring to a poisition of an object in a merkle tree,
# so that the Merkle proof verification algorithm knows what path to check the hashes against

# If all goes well, we'll update our light client memory with this header
# The header is the key trusted piece of data we use to verify merkle proofs against.
# From a beacon block, we can use merkle proofs to verify data about everything.  ie beacon state

class BeaconBlockHeader(Container):
  slot: Slot
  proposer_index: ValidatorIndex
  parent_root: Root
  state_root: Root
  body_root: Root

class ForkData(Container):
  current_version: Version
  genesis_validators_root: Root

class SigningData(Container):
  object_root: Root
  domain: Domain

class SyncAggregate(Container):
  sync_committee_bits: Bitvector[SYNC_COMMITTEE_SIZE]
  sync_committee_signature: BLSSignature

class SyncCommittee(Container):
  pubkeys: Vector[BLSPubkey, SYNC_COMMITTEE_SIZE]
  aggregate_pubkey: BLSPubkey

class LightClientBootstrap(Container):
  # The requested beacon block header
  header: BeaconBlockHeader
  # Current sync committee corresponding to `header`
  current_sync_committee: SyncCommittee
  current_sync_committee_branch: Vector[Bytes32, floorlog2(CURRENT_SYNC_COMMITTEE_INDEX)]


# This is the data we request to stay synced.  We need an update every time the slot increments.  (Different updates occur depending on the situation)
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
  # Slot at which the aggregate signature was created (untrusted)
  signature_slot: Slot

class LightClientFinalityUpdate(Container):
  # The beacon block header that is attested to by the sync committee
  attested_header: BeaconBlockHeader
  # The finalized beacon block header attested to by Merkle branch
  finalized_header: BeaconBlockHeader
  finality_branch: Vector[Bytes32, floorlog2(FINALIZED_ROOT_INDEX)]
  # Sync committee aggregate signature
  sync_aggregate: SyncAggregate
  # Slot at which the aggregate signature was created (untrusted)
  signature_slot: Slot

class LightClientOptimisticUpdate(Container):
  # The beacon block header that is attested to by the sync committee
  attested_header: BeaconBlockHeader
  # Sync committee aggregate signature
  sync_aggregate: SyncAggregate
  # Slot at which the aggregate signature was created (untrusted)
  signature_slot: Slot

@dataclass
class LightClientStore(object):
  # Beacon block header that is finalized (not expected to revert)
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