//
// Created by Aaryan Gulia on 19/01/2024.
//

#include "Blockchain.h"
#include "iostream"
#include <numeric>
#include "vector"
#include "fstream"

static int transactionID = 110000;
std::shared_ptr<Transaction> createTransaction(int& transactionID, double gas, double mev){
    std::shared_ptr<Transaction> transaction= std::make_shared<Transaction> (gas,mev,transactionID++);
    return transaction;
}

void Blockchain::startChainPosPbs(){
    for(int i = 0; i < chainSize; i++){
        for(int j = 0; j < 8; j++){
            std::uniform_real_distribution<double> distribution(0.0, 100.0);
            double gasFee = distribution(randomGenerator.rng);
            double mev = distribution(randomGenerator.rng) < 50 ? distribution(randomGenerator.rng) : 0.0;
            nodeFactory.addTransactionToNodes(createTransaction(transactionID, gasFee, mev));
        }
        for(auto& attacker : nodeFactory.attackers){
            attacker->clearAttacks();
        }
        std::cout<<"Block "<<i<<std::endl;
        auto proposer = nodeFactory.proposers[randomGenerator.genRandInt(0, nodeFactory.proposers.size() - 1)];
        proposer->runAuction();
        std::shared_ptr<Block> newBlock = proposer->proposedBlock;
        pbsBlocks.emplace_back(newBlock);
        auto builder = nodeFactory.builders[randomGenerator.genRandInt(0, nodeFactory.builders.size() - 1)];
        newBlock = builder->currBlock;
        newBlock -> proposerId = nodeFactory.proposers[randomGenerator.genRandInt(0, nodeFactory.proposers.size() - 1)]->id;
        posBlocks.emplace_back(newBlock);
        for_each(nodeFactory.builders.begin(),nodeFactory.builders.end(),
                 [&newBlock](std::shared_ptr<Builder> &b){b -> updateBids(newBlock -> bid);});
        for (const auto& transaction : newBlock->transactions) {
            nodeFactory.clearMempools(transaction);
        }
    }
}

void Blockchain::startChainPos(){
    for(int i = 0; i < chainSize; i++){
        for(int j = 0; j < 8; j++){
            std::uniform_real_distribution<double> distribution(0.0, 100.0);
            double gasFee = distribution(randomGenerator.rng);
            double mev = distribution(randomGenerator.rng) < 50 ? distribution(randomGenerator.rng) : 0.0;
            nodeFactory.addTransactionToNodes(createTransaction(transactionID, gasFee, mev));
        }
        for(auto& attacker : nodeFactory.attackers){
            attacker->clearAttacks();
        }
        std::cout<<"Block "<<i<<std::endl;
        auto builder = nodeFactory.builders[randomGenerator.genRandInt(0, nodeFactory.builders.size() - 1)];
        builder->buildBlock(10);
        std::shared_ptr<Block> newBlock = builder->currBlock;
        newBlock -> proposerId = nodeFactory.proposers[randomGenerator.genRandInt(0, nodeFactory.proposers.size() - 1)]->id;
        blocks.emplace_back(newBlock);
        for_each(nodeFactory.builders.begin(),nodeFactory.builders.end(),
                 [&newBlock](std::shared_ptr<Builder> &b){b -> updateBids(newBlock -> bid);});
        for (const auto& transaction : newBlock->transactions) {
            nodeFactory.clearMempools(transaction);
        }
    }
}

void Blockchain::startChain() {
    for(int i = 0; i < chainSize; i++){
        for(int j = 0; j < 8; j++){
            std::uniform_real_distribution<double> distribution(0.0, 100.0);
            double gasFee = distribution(randomGenerator.rng);
            double mev = distribution(randomGenerator.rng) < 50 ? distribution(randomGenerator.rng) : 0.0;
            nodeFactory.addTransactionToNodes(createTransaction(transactionID, gasFee, mev));
        }
        for(auto& attacker : nodeFactory.attackers){
            attacker->clearAttacks();
        }
        std::cout<<"Block "<<i<<std::endl;
        auto proposer = nodeFactory.proposers[randomGenerator.genRandInt(0, nodeFactory.proposers.size() - 1)];
        proposer->runAuction();
        std::shared_ptr<Block> newBlock = proposer->proposedBlock;
        blocks.emplace_back(newBlock);
        for_each(nodeFactory.builders.begin(),nodeFactory.builders.end(),
                 [&newBlock](std::shared_ptr<Builder> &b){b -> updateBids(newBlock -> bid);});
        for (const auto& transaction : newBlock->transactions) {
            nodeFactory.clearMempools(transaction);
        }
    }
}

void Blockchain::saveBlockData(){
    std::ofstream file;
    file.open("blockchain_data.csv");
    file<<"Block Number,Builder ID,Bid Value,Block Value,Reward"<<std::endl;
    for(int i = 0; i < blocks.size(); i++){
        file<<i<<","<<blocks[i] -> builderId<<","<<blocks[i]->bid<<","<<blocks[i]->blockValue<<","<<blocks[i]->blockValue-blocks[i]->bid<<std::endl;
    }
    file.close();
}

void Blockchain::saveBlockData(const std::string& filename, const std::vector<std::shared_ptr<Block>>& blocks) {
    std::ofstream file(filename);
    file << "Block Number,Proposer ID,Builder ID,Winning Bid Value,Winning Block Value,Reward";
    for(auto bid : blocks[0]->allBids){
        file << ",Builder ID " << bid.first << " Bid";
    }
    for(auto blockValue : blocks[0]->allBlockValues){
        file << ",Builder ID " << blockValue.first << " Block Value";
    }
    int blockNum = 0;
    for(const auto& block: blocks){
        blockNum++;
        file << "\n" << blockNum<<","<<block->proposerId <<"," <<block->builderId<<"," <<block->bid << "," << block->blockValue << "," << block->blockValue - block->bid;
        for(auto bid : block->allBids){
            file << "," << bid.second;
        }
        for(auto blockValue : block->allBlockValues){
            file << "," << blockValue.second;
        }

    }
}

void Blockchain::saveTrasactionData(const std::string& filename, const std::vector<std::shared_ptr<Block>>& blocks) {
    std::ofstream file(filename);

    // Write the header
    file << "Block ID,Block Bid,Builder ID,Block Value,Transaction ID,Transaction GAS,Transaction MEV\n";
    int blockId = 0;
    for (const auto& block : blocks) {
        blockId++;
        file << blockId<<"," << block->bid << "," << block->builderId<<","<<block->blockValue <<"\n";
        for (const auto& transaction : block->transactions) {
            file << "," << "," << "," << ","
                 << transaction->id << ","
                 << transaction->gas << ","
                 << transaction->mev << "\n";
        }
    }
    file.close();
}

void Blockchain::saveComparisonData(const std::string& filename) {
    std::ofstream file(filename);
    file << "Block Number,PBS Builder ID,POS Builder ID,Proposer ID,PBS Bid Value,PBS Block Value,POS Block Value,PBS Transaction ID,PBS Transaction GAS,PBS Transaction MEV,POS Transaction ID,POS Transaction GAS,POS Transaction MEV\n";
    for (int i = 0; i < pbsBlocks.size(); i++) {
        file << i+1 << "," << pbsBlocks[i]->builderId << ","<< posBlocks[i]->builderId << "," << pbsBlocks[i]->proposerId << "," << pbsBlocks[i]->bid << "," << pbsBlocks[i]->blockValue << "," << posBlocks[i]->blockValue << "\n";
        for(int j = 0; j < pbsBlocks[i]->transactions.size(); j++){
            file << "," << "," << "," << ","<<","<<","<<","
                 << pbsBlocks[i]->transactions[j]->id << ","
                 << pbsBlocks[i]->transactions[j]->gas << ","
                 << pbsBlocks[i]->transactions[j]->mev << ",";

            if(j < posBlocks[i]->transactions.size()){
                file << posBlocks[i]->transactions[j]->id << ","
                     << posBlocks[i]->transactions[j]->gas << ","
                     << posBlocks[i]->transactions[j]->mev << "\n";
            }
            else{
                file << ",,\n";
            }
        }
    }
}
