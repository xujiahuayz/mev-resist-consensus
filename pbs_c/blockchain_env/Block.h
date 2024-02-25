//
// Created by Aaryan Gulia on 26/01/2024.
//

#ifndef PBS_C_BLOCK_H
#define PBS_C_BLOCK_H
#include "Transaction.h"
#include "memory"
#include "vector"
#include "map"

class Block{
public:
    std::vector<std::shared_ptr<Transaction>> transactions;
    std::map<int,float> allBids;
    std::map<int,float> allBlockValues;
    int builderId;
    int proposerId;
    double bid;
    double blockValue;
    double gas;
    double mev;
};


#endif //PBS_C_BLOCK_H
