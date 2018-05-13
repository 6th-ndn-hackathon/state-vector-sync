import sys
import logging
import time
import random
import select
from pyndn import Name
from pyndn import Interest
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain
from pyndn.security import SafeBag
from pyndn.util import Blob
from svs.sync import StateVectorSync2018

def main():
    # check the same vector 1
    stateVector = {}
    receivedStateVector = {}
    assert(not mergeStateVector(stateVector, receivedStateVector));
    assert(stateVector == {});
    
    # check the same vector 2
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 10;
    stateVector["/user2"] = 1;
    receivedStateVector["/user1"] = 10;
    receivedStateVector["/user2"] = 1;
    assert(not mergeStateVector(stateVector, receivedStateVector));
    assert(stateVector == {'/user1': 10, '/user2': 1});
    
    # check new keys
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 10;
    stateVector["/user2"] = 1;
    receivedStateVector["/user1"] = 10;
    receivedStateVector["/user2"] = 1;
    receivedStateVector["/user3"] = 20;
    assert(mergeStateVector(stateVector, receivedStateVector));
    assert(stateVector == {'/user1': 10, '/user2': 1, '/user3': 20});
    
    # check updated values 1
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 9;
    stateVector["/user2"] = 1;
    receivedStateVector["/user1"] = 10;
    receivedStateVector["/user2"] = 1;
    assert(mergeStateVector(stateVector, receivedStateVector));
    assert(stateVector == {'/user1': 10, '/user2': 1});
    
    # check updated values 2
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 9;
    stateVector["/user2"] = 1;
    receivedStateVector["/user1"] = 10;
    receivedStateVector["/user2"] = 2;
    assert(mergeStateVector(stateVector, receivedStateVector));
    assert(stateVector == {'/user1': 10, '/user2': 2});
    
    # check updated values 3
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 9;
    stateVector["/user2"] = 2;
    receivedStateVector["/user1"] = 10;
    receivedStateVector["/user2"] = 1;
    assert(mergeStateVector(stateVector, receivedStateVector));
    assert(stateVector == {'/user1': 10, '/user2': 2});
    
    # mix scennario
    stateVector["/user1"] = 10;
    stateVector["/user2"] = 1;
    receivedStateVector["/user1"] = 9;
    receivedStateVector["/user2"] = 2;
    receivedStateVector["/user3"] = 20;
    assert(mergeStateVector(stateVector, receivedStateVector));
    assert(stateVector == {'/user1': 10, '/user2': 2, '/user3': 20});

    # Merge receivedStateVector into stateVector.
def mergeStateVector(myStateVector, receivedStateVector):
    updated = False;
    for k, v in receivedStateVector.items():
        if myStateVector.get(k) == None or myStateVector.get(k) < v:
            updated = True;
            myStateVector[k] = v;
    return updated;

main()
