//
// Created by Aaryan Gulia on 19/01/2024.
//

#include "Auction.h"
#include "iostream"
#include <time.h>
#include <thread>

Auction::Auction(BuilderFactory& mBuilderFactory, TransactionFactory &mTransactionFactory):
builderFactory(mBuilderFactory), transactionFactory(mTransactionFactory){}

void Auction::runAuction(){
    srand(time(NULL));
    auto endT = rand() % 24;
    for(int i = -1; i < endT; i++){
        builderFactory.propagateTransactions();
        std::for_each(builderFactory.builders.begin(), builderFactory.builders.end(),
                      [](std::shared_ptr<Builder>& builder) {
                          builder->buildBlock(10);
                      });
//        std::vector<std::thread> threads;
//        for (std::shared_ptr<Builder> builder : builderFactory.builders) {
//            threads.emplace_back([&builder]() {
//                builder->buildBlock(10);
//            });
//        }
//
//        for (std::thread& thread : threads) {
//            if (thread.joinable()) {
//                thread.join();
//            }
//        }
        std::shared_ptr<Builder> winningBuilder = *std::max_element(builderFactory.builders.begin(), builderFactory.builders.end(),
                                             [](std::shared_ptr<Builder> &a, std::shared_ptr<Builder> &b) {
                                                 return a -> currBid < b -> currBid; // Compare currBid values
                                             });
        auctionBlock = winningBuilder -> currBlock;

        if (winningBuilder->currBlock == nullptr){
            std::cout<<"Builder "<<winningBuilder->id<<" has mempool size "<<winningBuilder->mempool.size()<<std::endl;
            std::cerr << "Error: Winning builder does not have a current block."<<std::endl;
            return;
        }

    }

}