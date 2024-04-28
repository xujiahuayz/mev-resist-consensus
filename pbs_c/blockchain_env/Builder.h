//
// Created by Aaryan Gulia on 18/01/2024.
//

#ifndef PBS_C_BUILDER_H
#define PBS_C_BUILDER_H

#include "Transaction.h"
#include "Mempool.h"
#include "User.h"
#include "Block.h"
#include <map>
#include <tuple>
#include "mutex"
#include "Node.h"

struct KeyHash {
    std::size_t operator()(const std::tuple<double, int, std::vector<double>>& key) const {
        std::size_t seed = 0;
        seed ^= std::hash<double>()(std::get<0>(key)) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        seed ^= std::hash<int>()(std::get<1>(key)) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        for (double val : std::get<2>(key)) {
            seed ^= std::hash<double>()(val) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        }
        return seed;
    }
};

class Builder : virtual public Node {
protected:
    double blockValue;
    std::unordered_map<std::tuple<int,int, std::vector<double>>, std::pair<double, double>, KeyHash> findOptimalBidCache;
    Random randomEngine;
    std::vector<float> randomNumbers;
    int randomNumbersIndex;

public:


    std::vector<double> bids;
    std::shared_ptr<Block> currBlock;
    double currBid;
    int depth;
    int numSimulations;
    std::set<std::shared_ptr<Transaction>> lastMempool;

    Builder(int bId, double bCharacteristic, int bConnections, double bDepth, double bNumSim);
    Builder() : Node(-1,0,1) {}

    virtual void buildBlock(int maxBlockSize);

    virtual void buildBlock();
    void updateBids(double bid);
    double calculatedBid();

    double calculateUtility(double yourBid);
    double expectedUtility(double yourBid, std::vector<double> & bids);

    double expectedFutureUtility(double yourBid, int bDepth, double discountFactor, double bidIncrement, std::vector<double>& bids);
    std::pair<double, double> findOptimalBid(int bDepth, double discountFactor, double bidIncrement);


};


#endif //PBS_C_BUILDER_H
