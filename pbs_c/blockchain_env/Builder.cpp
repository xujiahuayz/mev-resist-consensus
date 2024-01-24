//
// Created by Aaryan Gulia on 18/01/2024.
//
#include "Builder.h"
#include "Random.h"
#include "Blockchain.h"
#include <iostream>


Builder::Builder(int bId, double bCharacteristic, Builder::Mempool bMempool, std::shared_ptr<Blockchain>  mBlockchain):
mempool(bMempool),id(bId),characteristic(bCharacteristic),currBid(0),
blockchain(mBlockchain){}

Builder::Builder(int bId, double bCharacteristic,std::shared_ptr<Blockchain>  mBlockchain):
        Builder(bId,bCharacteristic,Builder::Mempool{},mBlockchain){}

Builder::Builder(int bId,std::shared_ptr<Blockchain>  mBlockchain):
        Builder(bId,
                characteristic = randomGenerator.genRandLognormal(-1,0.2),
                Builder::Mempool{},mBlockchain){}


void Builder::buildBlock(){
    double sigma = 0.1;
    blockValue = randomGenerator.genRandNormal(characteristic, sigma);
}

void Builder::calculatedBid() {
    std::cout<<"Builder "<<id<<" is Calculating Bid ... "<<std::endl;
    std::vector<double> bids;
    std::transform(blockchain->blocks.begin(), blockchain->blocks.end(), std::back_inserter(bids),
                   [](const Blockchain::Block& block) { return block.bid; });
    int depth = 2;
    int numSimulations = 10;
    double discountFactor = 0.9;
    double bidIncrement = 1;

    // WE NEED TO DEFINE THE STRATEGY
    buildBlock();
    if(blockchain -> blocks.empty()) {
        currBid = randomGenerator.genRandInt(0,blockValue);
    }
    else {
        currBid = findOptimalFutureBid(numSimulations, depth, discountFactor,bidIncrement, bids).first;
    }
    std::cout<<"Builder "<<id<<" has Calculated Bid of "<<currBid<<std::endl;
}

double Builder::calculateUtility(double yourBid){
    return blockValue - yourBid;

}
double Builder::expectedUtility(double yourBid, int numSimulations){
    double totalUtility = 0;
    for(int i = 0; i < numSimulations; i++){
        int index = randomGenerator.genRandInt(0, blockchain -> blocks.size());
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

double Builder::expectedFutureUtility(double yourBid, int numSimulations, int depth, int discountFactor, int bidIncrement, std::vector<double> bids){
    double totalUtility = 0;
    if(depth == 0){
        totalUtility = expectedUtility(yourBid, numSimulations);
    }
    else {
        totalUtility += findOptimalFutureBid(numSimulations, --depth, discountFactor,bidIncrement, bids).second;
    }
    return totalUtility;
}

std::pair<double, double> Builder::findOptimalFutureBid(int numSimulations, int depth, int discountFactor, int bidIncrement, std::vector<double> bids){
    const double BID_INCREMENT = 0.5;
    const double DISCOUNT_FACTOR = 0.9; // Assuming a discount factor of 0.9
    double optimalBid = 0.0;
    double maxUtility = 0.0;
    if(blockValue > 0) {
        for (double bid = 0.0; bid <= blockValue; bid += BID_INCREMENT) {
            std::vector<double> testBids = bids;
            testBids.push_back(bid);
            double utility = expectedFutureUtility(bid, numSimulations, depth, discountFactor, bidIncrement, testBids);
            if (utility > maxUtility) {
                maxUtility = utility;
                optimalBid = bid;
            }
        }
    }
    return std::pair<double, double> (optimalBid, maxUtility);
}