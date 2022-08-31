**Install Dependencies**
Just enter in CLI:
     pip install -r requirements.txt

**Code is in light-client branch!**

The goal for this MVP light client is to track (in real time) the current head of Ethereum's blockchain in a 
computationally constrained environment.  Having the current block header allows you to verify that specific 
events/transactions have occured-  all without having to trust a 3rd party node operator to verify said  
transactions for you.

**Steps for Light Client:**
  1) Bootstrap to a period  --> 
  2) Sync from the bootstrapping period to the current period  -->
  3) Sync from the current period to the head of the chain  -->
  4) Continue staying synced to the head as new blocks are created

In order for the light client to execute these steps it must get its data from somewhere.  
The "Light Ethereum Subprotocol" (LES) is a network which serves said data to light clients in a client/server
architecture. Lodestar has an implementation of LES and is this light client's server.   


**Current Problems**
  - Update's next sync committee is rooted within the finalized header instead of its attested header.
    (This causes problems when the attested header falls ahead into the next sync period before the 
    update's finalized header is there)
    This bug is on Lodestar's end.  Smart people are on it as we speak!  
    https://github.com/ChainSafe/lodestar/issues/4426

  - py_ecc_bls.FastAggregateVerify() is throwing an assertion error when verifying the update's attested header.
    Basically, the sync committee's signatures aren't verifying that the attested header is legitimate.  This is
    a problem as this is the whole point of the light client.
    Within src/test.py you can find a test that shows the function itself works properly... So it must be
    a data problem, but I'm not sure where the problem lies. 


Introductory article on light clients:
https://mycelium.xyz/research/world-of-light-clients-ethereum

The single best resource I've found related to technical details on the Beacon Chain:
https://eth2book.info/altair/
