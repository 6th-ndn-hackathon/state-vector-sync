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
    assert(mergeStateVector(stateVector, receivedStateVector) == ([], False))
    assert(stateVector == {})
    
    # check the same vector 2
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 10
    stateVector["/user2"] = 1
    receivedStateVector["/user1"] = 10
    receivedStateVector["/user2"] = 1
    assert(mergeStateVector(stateVector, receivedStateVector) == ([], False))
    assert(stateVector == {'/user1': 10, '/user2': 1})
    
    # check new keys
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 10
    stateVector["/user2"] = 1
    receivedStateVector["/user1"] = 10
    receivedStateVector["/user2"] = 1
    receivedStateVector["/user3"] = 20
    assert(mergeStateVector(stateVector, receivedStateVector) == ([StateVectorSync2018.SyncState('/user3', 20)], False))
    assert(stateVector == {'/user1': 10, '/user2': 1, '/user3': 20})
    
    # check updated values 1
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 9
    stateVector["/user2"] = 1
    receivedStateVector["/user1"] = 10
    receivedStateVector["/user2"] = 1
    assert(mergeStateVector(stateVector, receivedStateVector) == ([StateVectorSync2018.SyncState('/user1', 10)], False))
    assert(stateVector == {'/user1': 10, '/user2': 1})
    
    # check updated values 2
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 9
    stateVector["/user2"] = 1
    receivedStateVector["/user1"] = 10
    receivedStateVector["/user2"] = 2
    assert(mergeStateVector(stateVector, receivedStateVector) == ([StateVectorSync2018.SyncState('/user1', 10), StateVectorSync2018.SyncState('/user2', 2)], False))
    assert(stateVector == {'/user1': 10, '/user2': 2})
    
    # check updated values 3
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 9
    stateVector["/user2"] = 2
    receivedStateVector["/user1"] = 10
    receivedStateVector["/user2"] = 1
    assert(mergeStateVector(stateVector, receivedStateVector) == ([StateVectorSync2018.SyncState('/user1', 10)], True))
    assert(stateVector == {'/user1': 10, '/user2': 2})
    
    # need to reply 1
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 10
    stateVector["/user2"] = 1
    assert(mergeStateVector(stateVector, receivedStateVector) == ([], True))
    assert(stateVector == {'/user1': 10, '/user2': 1})
    
    # need to reply 2
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 10
    stateVector["/user2"] = 1
    stateVector["/user3"] = 20
    receivedStateVector["/user1"] = 10
    receivedStateVector["/user2"] = 1
    assert(mergeStateVector(stateVector, receivedStateVector) == ([], True))
    assert(stateVector == {'/user1': 10, '/user2': 1, '/user3': 20})
    
    # mix scennario
    stateVector = {}
    receivedStateVector = {}
    stateVector["/user1"] = 10
    stateVector["/user2"] = 1
    receivedStateVector["/user1"] = 9
    receivedStateVector["/user2"] = 2
    receivedStateVector["/user3"] = 20
    assert(mergeStateVector(stateVector, receivedStateVector) == ([StateVectorSync2018.SyncState('/user2', 2), StateVectorSync2018.SyncState('/user3', 20)], True))
    assert(stateVector == {'/user1': 10, '/user2': 2, '/user3': 20})

    # Merge receivedStateVector into stateVector.
def mergeStateVector(myStateVector, receivedStateVector):
    needToReply = False
    result = []
    if myStateVector == receivedStateVector:
        return (result, needToReply)
    for k, v in receivedStateVector.items():
        if myStateVector.get(k) == None or myStateVector.get(k) < v:
            result.append(StateVectorSync2018.SyncState(k,v))
            myStateVector[k] = v
    for k, v in myStateVector.items():
        if receivedStateVector.get(k) == None or receivedStateVector.get(k) < v:
            needToReply = True
            break
    return (result, needToReply)

main()
