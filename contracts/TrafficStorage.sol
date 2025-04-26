// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract TrafficStorage {

    enum DataType { Data, Optimization }

    // Mapping: traffic_light_id => timestamp => DataType => CID
    mapping(string => mapping(uint256 => mapping(DataType => string))) private records;

    event RecordStored(string trafficLightId, uint256 timestamp, DataType dataType, string cid);

    /// @notice Store a new traffic or optimization record
    function storeRecord(
        string calldata trafficLightId,
        uint256 timestamp,
        DataType dataType,
        string calldata cid
    ) external {
        records[trafficLightId][timestamp][dataType] = cid;
        emit RecordStored(trafficLightId, timestamp, dataType, cid);
    }

    /// @notice Retrieve a record by traffic light, timestamp, and type
    function getRecord(
        string calldata trafficLightId,
        uint256 timestamp,
        DataType dataType
    ) external view returns (string memory) {
        string memory cid = records[trafficLightId][timestamp][dataType];
        require(bytes(cid).length > 0, "Record not found");
        return cid;
    }
}
