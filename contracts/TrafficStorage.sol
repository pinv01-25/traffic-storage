// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract TrafficStorage {
    string public ipfsCID; // Solo guardaremos 1 CID para la demo

    function storeCID(string memory _cid) public {
        ipfsCID = _cid;
    }

    function getCID() public view returns (string memory) {
        return ipfsCID;
    }
}
