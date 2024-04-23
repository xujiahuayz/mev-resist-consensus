//
// Created by Aaryan Gulia on 21/04/2024.
//

#include "ProposerBuilder.h"
#include <thread>
#include "factory/NodeFactory.h"

void runAuction(NodeFactory& nodeFactory, Proposer& proposer, Builder& builder){
    auto endT = randomGenerator.genRandInt(0, 24);
    for(int i = -1; i < endT; i++){
        nodeFactory.propagateTransactions();
        for(const auto& attacker: nodeFactory.attackers){
            attacker->attack();
        }
        std::vector<std::thread> threads;
        threads.reserve(nodeFactory.builders.size());
        for (const auto& builder : nodeFactory.builders) {
            threads.emplace_back([builder]() {
                builder->buildBlock(10);
            });
        }

        for (std::thread& thread : threads) {
            if (thread.joinable()) {
                thread.join();
            }
        }
        double maxBid = 0.0;
        std::vector<int> maxBidBuilders;
        for (int i = 0; i < nodeFactory.builders.size(); i++) {
            if (nodeFactory.builders[i]->currBid > maxBid) {
                maxBid = nodeFactory.builders[i]->currBid;
                maxBidBuilders.clear();
                maxBidBuilders.push_back(i);
            } else if (nodeFactory.builders[i]->currBid == maxBid) {
                maxBidBuilders.push_back(i);
            }
        }
        std::for_each(nodeFactory.builders.begin(), nodeFactory.builders.end(),
                      [&proposer](std::shared_ptr<Builder> &b){
                          proposer.currBids.emplace(std::pair<int,float>(b->id,b->currBid));
                          proposer.currBlockValues.emplace(std::pair<int,float>(b->id,b->currBlock->blockValue));
                      });

        Builder* winningBuilder = nodeFactory.builders[maxBidBuilders[randomGenerator.genRandInt(0, maxBidBuilders.size() - 1)]].get();
        if(winningBuilder->currBlock->bid < builder.currBlock->blockValue){
            winningBuilder = &builder;
            winningBuilder ->currBid = builder.currBlock->blockValue;
            winningBuilder ->currBlock->bid = builder.currBlock->blockValue;
        }
        proposer.propose(winningBuilder -> currBlock);
        proposer.currBids.clear();
        proposer.currBlockValues.clear();
        if (winningBuilder->currBlock == nullptr){
            std::cout<<"Builder "<<winningBuilder->id<<" has mempool size "<<winningBuilder->mempool.size()<<std::endl;
            std::cerr << "Error: Winning builder does not have a current block."<<std::endl;
            return;
        }
    }
}

void ProposerBuilder::runAuction() {
    ::runAuction(nodeFactory, *this, *this);
}

void ProposerAttackerBuilder::runAuction() {
    ::runAuction(nodeFactory, *this, *this);
}