//
// Created by Aaryan Gulia on 19/01/2024.
//

#ifndef PBS_C_BLOCKCHAIN_H
#define PBS_C_BLOCKCHAIN_H
#include "game_env/Auction.h"
#include "vector"
#include "Block.h"


class Blockchain {
    size_t chainSize;
public:
    NodeFactory nodeFactory;
    std::vector<std::shared_ptr<Block>> blocks;
    std::vector<std::shared_ptr<Block>> posBlocks;
    std::vector<std::shared_ptr<Block>> pbsBlocks;

    Blockchain(size_t bChainSize, NodeFactory nodeFactory):chainSize(bChainSize),nodeFactory(nodeFactory){};
    Blockchain(size_t bChainSize):Blockchain(bChainSize,NodeFactory()){};
    Blockchain();

    void startChain();
    void startChainPos();
    void startChainPbs();
    void printBlockStats();
    void saveBlockData(std::string filename, std::vector<std::shared_ptr<Block>> blocks, std::string type);
    void saveToCSV(const std::string& filename);
    void saveBlockData(const std::string& filename, const std::vector<std::shared_ptr<Block>>& blocks);
    void saveTrasactionData(const std::string& filename, const std::vector<std::shared_ptr<Block>>& blocks);
    void saveComparisonData(const std::string& filename);
};


#endif //PBS_C_BLOCKCHAIN_H
