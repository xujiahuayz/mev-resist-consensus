//
// Created by Aaryan Gulia on 18/01/2024.
//
#include "Builder.h"
#include "include/Random.cpp"
#include "Blockchain.h"
#include <iostream>


Builder::Builder(int bId, double bCharacteristic, Builder::Mempool bMempool, std::shared_ptr<Blockchain>  mBlockchain):
mempool(bMempool),id(bId),characteristic(bCharacteristic),currBid(0),
blockchain(mBlockchain){}

Builder::Builder(int bId, double bCharacteristic,std::shared_ptr<Blockchain>  mBlockchain):
        Builder(bId,bCharacteristic,Builder::Mempool{},mBlockchain){}

Builder::Builder(int bId,std::shared_ptr<Blockchain>  mBlockchain):
        Builder(bId,
                characteristic = genRandLognormal(-1,0.2),
                Builder::Mempool{},mBlockchain){}


void Builder::buildBlock(){
    double sigma = 0.1;
    blockValue = genRandNormal(characteristic, sigma);
}

void Builder::calculatedBid() {
    // WE NEED TO DEFINE THE STRATEGY
    buildBlock();
    if(blockchain -> blocks.empty()) {
        currBid = genRandInt(0,blockValue);
    }
    else {
        currBid = findOptimalBid(10);
    }
}

double Builder::calculateUtility(double yourBid){
    return blockValue - yourBid;

}
double Builder::expectedUtility(double yourBid, int numSimulations){
    double totalUtility = 0;
    for(int i = 0; i < numSimulations; i++){
        int index = genRandInt(0, blockchain -> blocks.size());
        double oppBid = blockchain -> blocks[index].bid;
        totalUtility += yourBid > oppBid? calculateUtility(yourBid) : 0;
    }
    return totalUtility/numSimulations;
}

double Builder::findOptimalBid(int numSimulations){
    const double BID_INCREMENT = 0.5;
    double optimalBid = 0.0;
    double maxUtility = 0.0;
    if(blockValue > 0) {
        for (double bid = 0.0; bid <= blockValue; bid += BID_INCREMENT) {
            double utility = expectedUtility(bid, numSimulations);
            if (utility > maxUtility) {
                maxUtility = utility;
                optimalBid = bid;
            }
        }
    }
    return optimalBid;
}