import time
from containers import (LightClientUpdate, genesis_validators_root,
                        MIN_GENESIS_TIME, 
                        uint64)
from api import (bootstrap_object,
                 trusted_block_root,
                 instantiate_sync_period_data,
                 instantiate_finality_update_data, 
                 instantiate_optimistic_update_data, 
                 updates_for_period)
from specfunctions import (compute_sync_committee_period_at_slot, 
                           initialize_light_client_store,
                           process_light_client_update,
                           process_light_client_finality_update,
                           process_light_client_optimistic_update, 
                           process_slot_for_light_client_store)
from helper import(call_api,
                   get_current_epoch,
                   get_current_slot,
                   get_current_sync_period,
)

def sync_to_current_period(light_client_store) -> int:
  light_client_update = LightClientUpdate() 
  sync_period = compute_sync_committee_period_at_slot(light_client_store.finalized_header.slot)     # Which variable should I use to compute the sync period?
  while 1>0:
    current_time = uint64(int(time.time()))
    current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
    updates = updates_for_period(sync_period)
 
    # This should be turned into its own function and reused inside of sync_to_current_updates 
    if updates.status_code == 200:
      light_client_update = instantiate_sync_period_data(updates.json())
      #  This function is the antithesis of what the project is converging towards
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root)                   
      time.sleep(1)
      sync_period += 1
    else:
      sync_period = sync_period - 1 
      return light_client_update


def sync_to_current_updates(light_client_store, light_client_update):          
  previous_sync_period = 0 
  previous_epoch = 0
  previous_slot = 0
  while 1>0:
    current_time = uint64(int(time.time()))                           
    current_slot = get_current_slot(current_time, MIN_GENESIS_TIME)
    current_epoch = get_current_epoch(current_time, MIN_GENESIS_TIME)
    current_sync_period = get_current_sync_period(current_time, MIN_GENESIS_TIME) 
    updates = updates_for_period(current_sync_period)
    
    #  Error occurs during the transition of periods:    "Exception: incorrect bitvector input: 1 bits, vector length is: 512"
    if current_sync_period - previous_sync_period == 1:
      light_client_update = instantiate_sync_period_data(updates.json()) 
      process_light_client_update(light_client_store, 
                                  light_client_update, 
                                  current_slot,
                                  genesis_validators_root)                   
    elif current_epoch - previous_epoch == 1:
      current_finality_update_message = call_api(current_finality_update_url).json()
      finality_update = instantiate_finality_update_data(current_finality_update_message) 
      process_light_client_finality_update(light_client_store, 
                                           finality_update, 
                                           current_slot, 
                                           genesis_validators_root) 

    elif current_slot - previous_slot == 1:
      current_header_update_message = call_api(current_header_update_url).json()                 
      process_slot_for_light_client_store(light_client_store, current_slot)               
      optimistic_update = instantiate_optimistic_update_data(current_header_update_message)     
      process_light_client_optimistic_update(light_client_store,
                                             optimistic_update,
                                             current_slot,
                                             genesis_validators_root) 


    previous_sync_period = current_sync_period
    previous_epoch = current_epoch 
    previous_slot = current_slot 
    time.sleep(1)
  return


# ================
# UPDATE VARIABLES
# ================
current_finality_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/light_client/finality_update/" 
current_header_update_url = "https://lodestar-mainnet.chainsafe.io/eth/v1/beacon/light_client/optimistic_update/" 

if __name__ == "__main__":
  """ 
    Step 1: Initialize the light client store
  """
  light_client_store = initialize_light_client_store(trusted_block_root, bootstrap_object)
   
  """  
    Step 2: Sync from bootstrap period to current period 
  """
  light_client_update = sync_to_current_period(light_client_store)
   
  """
   Step 3: Sync from current period to current finalized block header. 
   Keep up with the most recent finalized header (Maybe each slot if Lodestar's API is fire.  Ask Cayman)
  """
  sync_to_current_updates(light_client_store, light_client_update)