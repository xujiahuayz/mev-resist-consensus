//
// Created by Aaryan Gulia on 19/01/2024.
//

#include "Auction.h"
#include "iostream"
#include <thread>

void Auction::runAuction(){
    auto endT = randomGenerator.genRandInt(0, 24);
    for(int i = -1; i < endT; i++){
        nodeFactory.propagateTransactions();
        for(auto attacker: nodeFactory.attackers){
            attacker->attack();
        }
        std::vector<std::thread> threads;
        for (std::shared_ptr<Builder> builder : nodeFactory.builders) {
            threads.emplace_back([builder]() {
                builder->buildBlock(10);
            });
        }

        for (std::thread& thread : threads) {
            if (thread.joinable()) {
                thread.join();
            }
        }
        double maxBid = std::max_element(nodeFactory.builders.begin(), nodeFactory.builders.end(),
                                         [](std::shared_ptr<Builder> &a, std::shared_ptr<Builder> &b) {
                                             return a -> currBid < b -> currBid; // Compare currBid values
                                         })->get()->currBid;
        std::vector<std::shared_ptr<Builder>> maxBidBuilders;
        std::copy_if(nodeFactory.builders.begin(), nodeFactory.builders.end(), std::back_inserter(maxBidBuilders),
                     [maxBid](std::shared_ptr<Builder> &builder) {
                         return builder->currBid == maxBid;
                     });

        std::shared_ptr<Builder> winningBuilder = maxBidBuilders[randomGenerator.genRandInt(0, maxBidBuilders.size() - 1)];
        auctionBlock = winningBuilder -> currBlock;

        if (winningBuilder->currBlock == nullptr){
            std::cout<<"Builder "<<winningBuilder->id<<" has mempool size "<<winningBuilder->mempool.size()<<std::endl;
            std::cerr << "Error: Winning builder does not have a current block."<<std::endl;
            return;
        }

    }

}