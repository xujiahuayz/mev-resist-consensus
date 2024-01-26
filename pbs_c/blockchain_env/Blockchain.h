//
// Created by Aaryan Gulia on 19/01/2024.
//

#ifndef PBS_C_BLOCKCHAIN_H
#define PBS_C_BLOCKCHAIN_H
#include "game_env/Auction.h"
#include "vector"
#include "Block.h"
#include "factory/BuilderFactory.h"
#include "game_env/Attacker.h"

class Blockchain {
    size_t chainSize;
public:
    BuilderFactory builderFactory;
    std::vector<std::shared_ptr<Block>> blocks;
    TransactionFactory transactionFactory=TransactionFactory(100, 50);
    Blockchain(size_t bChainSize, size_t numBuilders);
    Blockchain(size_t bChainSize);
    Blockchain();

    void startChain();
    void printBlockStats();
    void saveBlockData();
    void saveToCSV(const std::string& filename);
};


#endif //PBS_C_BLOCKCHAIN_H
