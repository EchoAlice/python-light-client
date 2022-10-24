**Getting Started**\
Enter in CLI:    pip install -r requirements.txt

To run program: \
      - Working directory is:                            /python-light-client> \
      - Execute within terminal to run program:          src/main.py
         
**Summary**\
The original goal for this MVP light client was to track (in real time) the current head of Ethereum's blockchain in a 
computationally constrained environment.  Having the current block header allows you to verify that specific 
events/transactions have occured-  all without having to trust a 3rd party node operator to verify said  
transactions for you.  Use cases include browser wallets and trustless bridges.

In order for the light client to keep up with the current state of the chain it must receive data its data from somewhere.  
The "Light Ethereum Subprotocol" (LES) is a network which serves said data to light clients with a client/server
architecture. Lodestar has an implementation of LES and is this light client's server.   

While I love Lodestar, the client/server model for light clients isn't ideal.  Decentralizing the stack is always
the goal.  The Portal Network is a set of peer to peer networks that, among other things, is attempting to host 
the data needed to allow light clients to opperate. 
\

**The refined goal for this light client is to track the current head of the Beacon chain via the Portal Netork.**
\

Starting points for updated goal: \
https://github.com/ethereum/portal-network-specs/pull/166 \
https://github.com/ogenev/portal-network-specs/tree/beacon-lc-network-specs/beacon-chain \


**Steps for Light Client:**
  1) Bootstrap to a period  --> 
  2) Sync from the bootstrapping period to the current period  -->
  3) Sync from the current period to the head of the chain  -->
  4) Continue staying synced to the head as new blocks are created


**Current Problems**
  - Update's next sync committee is rooted within the finalized header instead of its attested header.
    This causes problems when the attested header falls ahead into the next sync period before the 
    update's finalized header is there
     Lodestar fixed the issue, but my next sync committee is still rooted in finalized header, 
     instead of attested header  --> https://github.com/ChainSafe/lodestar/issues/4426

  - Solved the py_ecc.bls library bug (I was passing in an SSZ byte array into the signature verification function instead 
    of passing in bytes).  Figured it out by using the Milagro bls library.  It threw an error telling me to use bytes!
    But now I've got another mysterious assertion error that comes up after verifying 3 periods worth of committee changes.


**To Do**
  - Track down another assertion error with bls library
  - Figure out logic for syncing to the current block and place it inside of main.py
  - Transition from Lodestar to Portal Network

***My diagrams of Light Clients and the syncing process (Work In Progress):***
https://miro.com/app/board/uXjVOjfZyhU=/?share_link_id=526682350813

***Other Resources***\
Introductory article on light clients: \
https://mycelium.xyz/research/world-of-light-clients-ethereum

Best resource on the Beacon Chain: \
https://eth2book.info/altair/