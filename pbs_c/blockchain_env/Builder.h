//
// Created by Aaryan Gulia on 18/01/2024.
//

#ifndef PBS_C_BUILDER_H
#define PBS_C_BUILDER_H

#include "Transaction.h"
#include "Mempool.h"
#include "User.h"

class Blockchain;

class Builder {
    friend class Blockchain;
    std::shared_ptr<Blockchain> blockchain;
private:
    typedef std::vector<Transaction> Mempool;
    Mempool mempool;
    double characteristic;
    double blockValue;


public:
    double currBid;
    int id;
    Builder(int bId, double bCharacteristic, Mempool bMempool, std::shared_ptr<Blockchain> mBlockchain);
    Builder(int bId, double bCharacteristic, std::shared_ptr<Blockchain>  mBlockchain);
    Builder(int bId, std::shared_ptr<Blockchain>  mBlockchain);
    Builder() : blockchain(nullptr) {}

    void buildBlock();
    void calculatedBid();
    void updateBid();

    double calculateUtility(double yourBid);
    double expectedUtility(double yourBid, int numSimulations);
    double findOptimalBid(int numSimulations);


};


#endif //PBS_C_BUILDER_H
