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
        builderFactory.addBuilder(builderFactory.createBuilder(i+1));
    }
    builderFactory.assignNeighbours(2);
}
Blockchain::Blockchain(size_t bChainSize):Blockchain(bChainSize,100) {}
Blockchain::Blockchain():Blockchain(100,100){}


void Blockchain::startChain() {
    Attacker attacker(transactionFactory);
    for(int i = 0; i < chainSize; i++){
        attacker.attack(i+1);
        transactionFactory.createTransactions(i+1);
        builderFactory.addTransactionsToBuilder(transactionFactory);
        std::cout<<"Block "<<i<<std::endl;
        Auction auction(builderFactory, transactionFactory);
        auction.runAuction();
        std::shared_ptr<Block> newBlock = auction.auctionBlock;
        blocks.emplace_back(newBlock);
        for_each(builderFactory.builders.begin(),builderFactory.builders.end(),
                 [&auction](std::shared_ptr<Builder> &b){b -> updateBids(auction.auctionBlock -> bid);});
        for (const auto& transaction : newBlock->transactions) {
            for (auto& builder : builderFactory.builders) {
                builder->mempool.erase(std::remove_if(builder->mempool.begin(), builder->mempool.end(),
                                                      [&](const std::shared_ptr<Transaction>& t) { return t->id == transaction->id; }),
                                       builder->mempool.end());
            }
            transactionFactory.transactions.erase(std::remove_if(transactionFactory.transactions.begin(), transactionFactory.transactions.end(),
                                                                 [&](const Transaction& t) { return t.id == transaction->id; }),
                                                  transactionFactory.transactions.end());
        }
    }
    attacker.results(blocks);
}


void Blockchain::printBlockStats() {
    auto avgBid = std::reduce(blocks.begin(),blocks.end(),0.0,
                           [](double a, std::shared_ptr<Block> &b){return a + b -> bid;})/blocks.size();
    std::cout<<"The Average Winnig Bid is: "<<avgBid<<std::endl;
    auto avgReward = std::reduce(blocks.begin(),blocks.end(),0.0,
                              [](double a, std::shared_ptr<Block> &b){return a + (b->blockValue - b->bid);})/blocks.size();
    std::cout<<"The Average Reward is: "<<avgReward<<std::endl;
    std::unordered_map<size_t, size_t> freqMap(builderFactory.builders.size());
    std::for_each(blocks.begin(),blocks.end(),[&freqMap](std::shared_ptr<Block> &a){
        ++(freqMap[a -> builderId]);
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
        file<<i<<","<<blocks[i] -> builderId<<","<<blocks[i]->bid<<","<<blocks[i]->blockValue<<","<<blocks[i]->blockValue-blocks[i]->bid<<std::endl;
    }
    file.close();
}
void Blockchain::saveToCSV(const std::string& filename) {
    std::ofstream file(filename);

    // Write the header
    file << "Block ID,Transaction ID,Transaction GAS,Transaction MEV\n";
    int blockId = 0;
    for (const auto& block : blocks) {
        blockId++;
        for (const auto& transaction : block->transactions) {
            file << blockId << ","
                 << transaction->id << ","
                 << transaction->gas << ","
                 << transaction->mev << "\n";;
        }
    }

    file.close();
}