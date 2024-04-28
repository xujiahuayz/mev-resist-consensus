//
// Created by Aaryan Gulia on 21/04/2024.
//

#include "ProposerBuilder.h"
#include <thread>
#include "factory/NodeFactory.h"

void runAuction(NodeFactory& nodeFactory, Proposer& proposer, Builder& builder){
    auto endT = randomGenerator.genRandInt(0, 24);
    nodeFactory.propagateTransactionsParallel();
    for(int i = -1; i < endT; i++){
        for(const auto& attacker: nodeFactory.attackers){
            attacker->attack();
        }
        if(i == endT-1)
        {

            int numThreads = std::thread::hardware_concurrency();
            std::vector<std::thread> threads(numThreads);
            int buildersPerThread = nodeFactory.builders.size() / numThreads;

            for (int i = 0; i < numThreads; ++i) {
                threads[i] = std::thread([&nodeFactory, i, buildersPerThread]() {
                    for (int j = i * buildersPerThread; j < (i + 1) * buildersPerThread && j < nodeFactory.builders.size(); ++j) {
                        nodeFactory.builders[j]->buildBlock(10);
                        nodeFactory.builders[j]->currBlock -> bid = nodeFactory.builders[j]->calculatedBid();
                    }
                });
            }

            // Handle remaining builders if builders.size() is not a multiple of numThreads
            for (int i = numThreads * buildersPerThread; i < nodeFactory.builders.size(); ++i) {
                nodeFactory.builders[i]->buildBlock(10);
                nodeFactory.builders[i]->currBlock -> bid = nodeFactory.builders[i]->calculatedBid();
            }

            for (std::thread &thread: threads) {
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
                          [&proposer](std::shared_ptr<Builder> &b) {
                              proposer.currBids.emplace(std::pair<int, float>(b->id, b->currBid));
                              proposer.currBlockValues.emplace(std::pair<int, float>(b->id, b->currBlock->blockValue));
                          });

            Builder *winningBuilder = nodeFactory.builders[maxBidBuilders[randomGenerator.genRandInt(0,
                                                                                                     maxBidBuilders.size() -
                                                                                                     1)]].get();
            if (winningBuilder->currBlock->bid < builder.currBlock->blockValue) {
                winningBuilder = &builder;
                winningBuilder->currBid = builder.currBlock->blockValue;
                winningBuilder->currBlock->bid = builder.currBlock->blockValue;
            }
            proposer.propose(winningBuilder->currBlock);
            proposer.currBids.clear();
            proposer.currBlockValues.clear();
            if (winningBuilder->currBlock == nullptr) {
                std::cout << "Builder " << winningBuilder->id << " has mempool size " << winningBuilder->mempool.size()
                          << std::endl;
                std::cerr << "Error: Winning builder does not have a current block." << std::endl;
                return;
            }
        }
    }
}

void ProposerBuilder::runAuction(NodeFactory& nodeFactory) {
    ::runAuction(nodeFactory, *this, *this);
}

void ProposerAttackerBuilder::runAuction(NodeFactory& nodeFactory) {
    ::runAuction(nodeFactory, *this, *this);
}