//
// Created by Aaryan Gulia on 16/02/2024.
//

#include "AttackerBuilder.h"

AttackerBuilder::AttackerBuilder(size_t abId, int abConnections, double abCharacteristic, double abDepth,
                                 double abNumSim): Builder(abId, abCharacteristic,abConnections, abDepth, abNumSim),Node(abId, abConnections, abCharacteristic) {
}

void AttackerBuilder::buildBlock(int maxBlockSize){
    std::vector<std::shared_ptr<Transaction>> sortedMempool(mempool.begin(), mempool.end());
    std::sort(sortedMempool.begin(), sortedMempool.end(), [](const std::shared_ptr<Transaction>& a, const std::shared_ptr<Transaction>& b) {
        return a->gas > b->gas;
    });
    std::vector<std::shared_ptr<Transaction>> mevSortedMempool(mempool.begin(), mempool.end());
    std::sort(mevSortedMempool.begin(), mevSortedMempool.end(), [](const std::shared_ptr<Transaction>& a, const std::shared_ptr<Transaction>& b) {
        return a->mev > b->mev;
    });
    Block block;
    block.blockValue = 0;
    auto gasPtr = sortedMempool.begin();
    auto mevPtr = mevSortedMempool.begin();
    while(block.transactions.size()<=maxBlockSize) {
        if(gasPtr == sortedMempool.end() && mevPtr == mevSortedMempool.end()){
            break;
        }
        if(gasPtr == sortedMempool.end()){
            block.transactions.push_back(std::make_shared<Transaction>(
                    Transaction(0, 0, id * 1000 + attackCounter)));
            block.transactions.push_back(*mevPtr);
            block.transactions.push_back(std::make_shared<Transaction>(
                    Transaction(0, 0, -1 * (id * 1000 + attackCounter++))));
            block.blockValue += (*mevPtr)->gas;
            block.blockValue += (*mevPtr)->mev;
            mevPtr++;
            continue;
        }
        if(mevPtr == mevSortedMempool.end()){
            auto gasTrans = std::find(block.transactions.begin(), block.transactions.end(), *gasPtr);
            if(gasTrans == block.transactions.end()){
                block.transactions.push_back(*gasPtr);
                block.blockValue += (*gasPtr)->gas;
            }
            gasPtr++;
            continue;
        }

        double compGas = 0;
        for(int j = 0; j < 3; j++){
            if(gasPtr+j == sortedMempool.end()){
                break;
            }
            compGas += (*(gasPtr+j))->gas;
        }
        if(compGas < (*mevPtr)->mev + (*mevPtr)->gas){
            auto mevTrans = std::find(block.transactions.begin(), block.transactions.end(), *mevPtr);
            if(mevTrans == block.transactions.end() && block.transactions.size()+3<=maxBlockSize){
                block.transactions.push_back(std::make_shared<Transaction>(
                        Transaction(0, 0, id * 1000 + attackCounter)));
                block.transactions.push_back(*mevPtr);
                block.transactions.push_back(std::make_shared<Transaction>(
                        Transaction(0, 0, -1*(id * 1000 + attackCounter++))));
                block.blockValue += (*mevPtr)->gas;
                block.blockValue += (*mevPtr)->mev;
                mevPtr++;
            }
            else if(mevTrans != block.transactions.end() && block.transactions.size()+2<=maxBlockSize){
                auto it = block.transactions.emplace(mevTrans+1, std::make_shared<Transaction>(
                        Transaction(0, 0, id * 1000 + attackCounter)));
                block.transactions.emplace(it-1, std::make_shared<Transaction>(
                        Transaction(0, 0, -1*(id * 1000 + attackCounter++))));
                block.blockValue += (*mevPtr)->mev;
                mevPtr++;
            }
            else{
                auto gasTrans = std::find(block.transactions.begin(), block.transactions.end(), *gasPtr);
                if(gasTrans == block.transactions.end()){
                    block.transactions.push_back(*gasPtr);
                    block.blockValue += (*gasPtr)->gas;
                }
                gasPtr++;
                mevPtr = mevSortedMempool.end();
            }
        }
        else{
            auto gasTrans = std::find(block.transactions.begin(), block.transactions.end(), *gasPtr);
            if(gasTrans == block.transactions.end()){
                block.transactions.push_back(*gasPtr);
                block.blockValue += (*gasPtr)->gas;
            }
            gasPtr++;
        }
    }

    blockValue = block.blockValue;
    block.builderId = id;
    currBlock = std::make_shared<Block>(block);
    lastMempool = mempool;
    if(currBlock == nullptr){
        std::cerr<<"Error: Builder "<<id<<" does not have a current block!!!"<<std::endl;
    }
}