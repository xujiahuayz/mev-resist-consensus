//
// Created by Aaryan Gulia on 19/01/2024.
//

#ifndef PBS_C_BLOCKCHAIN_H
#define PBS_C_BLOCKCHAIN_H
#include "game_env/Auction.h"
#include "vector"

class Blockchain {
    size_t chainSize;
public:
    Auction::BuilderMap builders;
    struct Block{
        Builder* builder;
        double bid;
        double blockValue;
        double gas;
        double mev;
    };
    std::vector<Block> blocks;
    Blockchain(size_t bChainSize, size_t numBuilders);
    Blockchain(size_t bChainSize);
    Blockchain();

    void startChain();
    void printBlockStats();
    void saveBlockData();

    ~Blockchain();
};


#endif //PBS_C_BLOCKCHAIN_H
