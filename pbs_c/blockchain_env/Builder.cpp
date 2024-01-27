//
// Created by Aaryan Gulia on 18/01/2024.
//
#include "Builder.h"
#include "Blockchain.h"
#include <iostream>
#include <vector>

Builder::Builder(int bId, double bCharacteristic, std::vector<std::shared_ptr<Transaction>> bMempool, std::shared_ptr<Blockchain>  mBlockchain):
mempool(bMempool),id(bId),characteristic(bCharacteristic),currBid(0),
blockchain(mBlockchain){}

Builder::Builder(int bId, double bCharacteristic,std::shared_ptr<Blockchain>  mBlockchain):
        Builder(bId,bCharacteristic,std::vector<std::shared_ptr<Transaction>>{},mBlockchain){}

Builder::Builder(int bId,std::shared_ptr<Blockchain>  mBlockchain):
        Builder(bId,
                characteristic = randomGenerator.genRandLognormal(-1,0.2),
                std::vector<std::shared_ptr<Transaction>>{},mBlockchain){}


void Builder::buildBlock(){
    double sigma = 0.1;
    blockValue = randomGenerator.genRandNormal(characteristic, sigma);
}
void Builder::updateBids(double bid){
    bids.push_back(bid);
}

void Builder::calculatedBid() {
    //std::cout<<"Builder "<<id<<" is Calculating Bid ... "<<std::endl;
    int depth = 1;
    int numSimulations = 10;
    double discountFactor = 0.9;
    double bidIncrement = 0.5;

    if(bids.empty()) {
        currBid = randomGenerator.genRandInt(0,blockValue);
    }
    else {
        currBid = findOptimalBid(numSimulations, depth, discountFactor,bidIncrement).first;
    }
    //std::cout<<"Builder "<<id<<" has Calculated Bid of "<<currBid<<std::endl;
}

double Builder::calculateUtility(double yourBid){
    return blockValue - yourBid;
}

double Builder::expectedUtility(double yourBid, int numSimulations, std::vector<double>& testBids){
    double totalUtility = 0;
    for(int i = 0; i < numSimulations; i++){
        double oppBid = testBids[randomGenerator.genRandInt(0, testBids.size()-2)];
        totalUtility += yourBid > oppBid? calculateUtility(yourBid) : 0;
    }
    return totalUtility/numSimulations;
}

double Builder::expectedFutureUtility(double yourBid, int numSimulations, int depth, double discountFactor, double bidIncrement,std::vector<double> & testBids){
    if(depth == 0){
        double totalUtility = expectedUtility(yourBid, numSimulations, testBids);
        return totalUtility;
    }
    else {
        double totalUtility = findOptimalBid(numSimulations, --depth, discountFactor,bidIncrement).second;
        totalUtility += expectedUtility(yourBid, numSimulations, testBids);
        return totalUtility;
    }
}

std::pair<double, double> Builder::findOptimalBid(int numSimulations, int depth, double discountFactor, double bidIncrement){
    double optimalBid = 0.0;
    double maxUtility = 0.0;
    if(blockValue > 0) {
        for (double bid = 0.0; bid <= blockValue; bid += bidIncrement) {
            //the below two lines can be removed to reduce latency
            std::vector<double> testBids = bids;
            testBids.push_back(bid);
            double utility = expectedUtility(bid, numSimulations, testBids);
            if (utility > maxUtility) {
                maxUtility = utility;
                optimalBid = bid;
            }
        }
        for(double bid = optimalBid; bid >= 0; bid -= bidIncrement){
            std::vector<double> testBids = bids;
            testBids.push_back(bid);
            double utility = expectedFutureUtility(bid, numSimulations, depth, discountFactor, bidIncrement, testBids);
            if (utility > maxUtility) {
                maxUtility = utility;
                optimalBid = bid;
            }
            else{
                break;
            }
        }
    }

    return std::pair<double, double> (optimalBid, maxUtility);
}

void Builder::buildBlock(int maxBlockSize) {
    std::sort(mempool.begin(), mempool.end(), [](const std::shared_ptr<Transaction>& a, const std::shared_ptr<Transaction>& b) {
        return a->gas > b->gas;
    });
    Block block;
    block.blockValue = 0;
    for (int i = 0; i < std::min(maxBlockSize, static_cast<int>(mempool.size())); ++i) {
        block.transactions.push_back(mempool[i]);
        block.blockValue += mempool[i]->gas;
    }
    blockValue = block.blockValue;
    calculatedBid();
    block.bid = currBid;
    block.builderId = id;
    currBlock = std::make_shared<Block>(block);
    if(currBlock == nullptr){
        std::cerr<<"Error: Builder "<<id<<" does not have a current block!!!"<<std::endl;
    }
}