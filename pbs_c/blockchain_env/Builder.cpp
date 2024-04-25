//
// Created by Aaryan Gulia on 18/01/2024.
//
#include "Builder.h"
#include "Blockchain.h"
#include "RandomNumberData.h"
#include <iostream>
#include <vector>
#include <fstream>

Builder::Builder(int bId, double bCharacteristic, int bConnections, double bDepth, double bNumSim):Node(bId, bConnections, bCharacteristic){
    depth = bDepth;
    numSimulations = bNumSim;
    randomNumbersIndex = randomEngine.genRandInt(0, 100000000-1);
}

void Builder::buildBlock(){
    double sigma = 0.1;
    blockValue = randomEngine.genRandNormal(characteristic, sigma);
}
void Builder::updateBids(double bid){
    bids.push_back(bid);
    if(bids.size()>100){
        bids.erase(bids.begin());
    }
}

void Builder::calculatedBid() {
    //std::cout<<"Builder "<<id<<" is Calculating Bid ... "<<std::endl;

    if(bids.empty()) {
        currBid = randomEngine.genRandInt(0,blockValue);
    }
    else {
        double discountFactor = 0.9;
        double bidIncrement = 0.5;
        currBid = findOptimalBid(depth,discountFactor,bidIncrement).first;
    }
    //std::cout<<"Builder "<<id<<" has Calculated Bid of "<<currBid<<std::endl;
}

double Builder::calculateUtility(double yourBid){
    return blockValue - yourBid;
}


double Builder::expectedUtility(double yourBid,std::vector<double>& testBids){

    double totalUtility = 0;
    for(int i = 0; i < numSimulations; i++){
        if (randomNumbersIndex >= randomNumbers.size()) {
            // If we have, wrap around to the start of the vector
            randomNumbersIndex = 0;
        }
        RandomNumberData* randomNumberData = RandomNumberData::getInstance();
        std::vector<float>& randomNumbers = randomNumberData->getRandomNumbers();
        int index = randomNumbers[randomNumbersIndex++];
        while(index >= testBids.size()){
            index = randomNumbers[randomNumbersIndex++];
        }
        double oppBid = testBids[index];
        totalUtility += yourBid > oppBid? calculateUtility(yourBid) : 0;
    }
    double result = totalUtility/numSimulations;

    return result;
}

double Builder::expectedFutureUtility(double yourBid, int bDepth, double discountFactor, double bidIncrement,std::vector<double> & testBids){
    if(bDepth == 0){
        double totalUtility = expectedUtility(yourBid,testBids);
        return totalUtility;
    }
    else {
        double totalUtility = findOptimalBid(--bDepth, discountFactor,bidIncrement).second;
        totalUtility += expectedUtility(yourBid, testBids);
        return totalUtility;
    }
}

std::pair<double, double> Builder::findOptimalBid(int bDepth, double discountFactor, double bidIncrement){
    // Create a tuple of the function's parameters
    std::tuple<int, int,std::vector<double>> key = std::make_tuple(bDepth,blockValue, bids);

    // Check if the result is already in the cache
    auto it = findOptimalBidCache.find(key);
    if (it != findOptimalBidCache.end()) {
        // If the result is in the cache, return it
        return it->second;
    }

    // If the result is not in the cache, compute it
    double optimalBid = 0.0;
    double maxUtility = 0.0;
    if(blockValue > 0) {
        for (double bid = 0.0; bid <= blockValue; bid += bidIncrement) {
            bids.push_back(bid);
            double utility = expectedUtility(bid,bids);
            if (utility > maxUtility) {
                maxUtility = utility;
                optimalBid = bid;
            }
            bids.pop_back();
        }
        for(double bid = optimalBid; bid >= 0 && bDepth !=0; bid -= bidIncrement){
            std::vector<double> testBids = bids;
            testBids.push_back(bid);
            double utility = expectedFutureUtility(bid, bDepth, discountFactor, bidIncrement, testBids);
            if (utility > maxUtility) {
                maxUtility = utility;
                optimalBid = bid;
            }
            else{
                break;
            }
        }
    }

    std::pair<double, double> result = std::pair<double, double> (optimalBid, maxUtility);

    // Store the result in the cache
    findOptimalBidCache[key] = result;

    return result;
}

void Builder::buildBlock(int maxBlockSize) {
    std::vector<std::shared_ptr<Transaction>> sortedMempool(mempool.begin(), mempool.end());
    std::sort(sortedMempool.begin(), sortedMempool.end(), [](const std::shared_ptr<Transaction>& a, const std::shared_ptr<Transaction>& b) {
        return a->gas > b->gas;
    });
    Block block;
    block.blockValue = 0;
    for (int i = 0; i < std::min(maxBlockSize, static_cast<int>(sortedMempool.size())); ++i) {
        block.transactions.push_back(sortedMempool[i]);
        block.blockValue += sortedMempool[i]->gas;
    }
    blockValue = block.blockValue;
    calculatedBid();
    block.bid = currBid;
    block.builderId = id;
    currBlock = std::make_shared<Block>(block);
    lastMempool = mempool;

    if(currBlock == nullptr){
        std::cerr<<"Error: Builder "<<id<<" does not have a current block!!!"<<std::endl;
    }
}