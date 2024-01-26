//
// Created by Aaryan Gulia on 18/01/2024.
//

#ifndef PBS_C_BUILDER_H
#define PBS_C_BUILDER_H

#include "Transaction.h"
#include "Mempool.h"
#include "User.h"
#include "Block.h"

class Blockchain;

class Builder {
    friend class Blockchain;
    std::shared_ptr<Blockchain> blockchain;
private:
    double characteristic;
    double blockValue;


public:
    std::vector<std::shared_ptr<Transaction>> mempool;
    std::vector<double> bids;
    std::shared_ptr<Block> currBlock;
    double currBid;
    int id;
    std::vector<std::shared_ptr<Builder>> adjBuilders;
    Builder(int bId, double bCharacteristic, std::vector<std::shared_ptr<Transaction>> bMempool, std::shared_ptr<Blockchain> mBlockchain);
    Builder(int bId, double bCharacteristic, std::shared_ptr<Blockchain>  mBlockchain);
    Builder(int bId, std::shared_ptr<Blockchain>  mBlockchain);
    Builder(int bId, double bCharacteristic): Builder(bId, bCharacteristic, nullptr){}
    Builder(int bId): Builder(bId, nullptr){}
    Builder() : blockchain(nullptr) {}

    void buildBlock(int maxBlockSize);

    void buildBlock();
    void updateBids(double bid);
    void calculatedBid();

    double calculateUtility(double yourBid);
    double expectedUtility(double yourBid, int numSimulations, std::vector<double> & bids);

    double expectedFutureUtility(double yourBid, int numSimulations, int depth, double discountFactor, double bidIncrement, std::vector<double>& bids);
    std::pair<double, double> findOptimalBid(int numSimulations, int depth, double discountFactor, double bidIncrement);


};


#endif //PBS_C_BUILDER_H
