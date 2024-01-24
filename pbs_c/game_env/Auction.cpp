//
// Created by Aaryan Gulia on 19/01/2024.
//

#include "Auction.h"
#include "iostream"
#include <time.h>
#include <thread>

Auction::Auction(BuilderMap &aBuilders):builders(aBuilders){}

void Auction::runAuction(){
    srand(time(NULL));
    auto endT = rand() % 24;
    endT = 0;
    for(int i = -1; i < endT; i++){
        std::vector<std::thread> threads;
        for (Builder& builder : builders) {
            threads.emplace_back([&builder]() {
                builder.calculatedBid();
            });
        }

        for (std::thread& thread : threads) {
            if (thread.joinable()) {
                thread.join();
            }
        }
        winningBuilder = &(*std::max_element(builders.begin(), builders.end(),
                                             [](const Builder &a, const Builder &b) {
                                                 return a.currBid < b.currBid; // Compare currBid values
                                             }));
        maxBid = winningBuilder -> currBid;
    }

}