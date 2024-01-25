//
// Created by Aaryan Gulia on 19/01/2024.
//

#include "Blockchain.h"
#include "iostream"
#include <numeric>
#include "vector"
#include "fstream"

Blockchain::Blockchain(size_t bChainSize, size_t numBuilders):chainSize(bChainSize){
    for(int i = 0; i < numBuilders; i++){
        std::shared_ptr<Blockchain> iBlockchain(this);
        Builder nBuilder(i,iBlockchain);
        builders.emplace_back(nBuilder);
    }
}
Blockchain::Blockchain(size_t bChainSize):Blockchain(bChainSize,100) {}
Blockchain::Blockchain():Blockchain(100,100){}
Blockchain::~Blockchain() {
    for (auto& block : blocks) {
        delete block.builder;
    }
}

void Blockchain::startChain() {
    for(int i = 0; i < chainSize; i++){
        Auction auction(builders);
        auction.runAuction();
        Block newBlock;
        newBlock.builder = new Builder(*auction.winningBuilder);
        newBlock.bid = auction.maxBid;
        newBlock.blockValue = newBlock.builder -> blockValue;
        blocks.emplace_back(newBlock);
    }
}


void Blockchain::printBlockStats() {
    auto avgBid = std::reduce(blocks.begin(),blocks.end(),0.0,
                           [](double a, Block &b){return a + b.bid;})/blocks.size();
    std::cout<<"The Average Winnig Bid is: "<<avgBid<<std::endl;
    auto avgReward = std::reduce(blocks.begin(),blocks.end(),0.0,
                              [](double a, Block &b){return a + (b.blockValue - b.bid);})/blocks.size();
    std::cout<<"The Average Reward is: "<<avgReward<<std::endl;
    std::unordered_map<size_t, size_t> freqMap(builders.size());
    std::for_each(blocks.begin(),blocks.end(),[&freqMap](Block &a){
        ++(freqMap[a.builder -> id]);
    });
    for(const auto &b : freqMap){
        std::cout<<"Builder "<<b.first<<" Won "<<b.second<<" Times"<<std::endl;
    }
}

void Blockchain::saveBlockData(){
    std::ofstream file;
    file.open("blockchain_data.csv");
    file<<"Block Number,Builder ID,Bid Value,Block Value,Reward"<<std::endl;
    for(int i = 0; i < blocks.size(); i++){
        file<<i<<","<<blocks[i].builder -> id<<","<<blocks[i].bid<<","<<blocks[i].blockValue<<","<<blocks[i].blockValue-blocks[i].bid<<std::endl;
    }
    file.close();
}