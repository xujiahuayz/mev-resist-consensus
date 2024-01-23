//
// Created by Aaryan Gulia on 19/01/2024.
//

#include "Auction.h"
#include "iostream"
#include <time.h>

Auction::Auction(BuilderMap &aBuilders):builders(aBuilders){}

void Auction::runAuction(){
    srand(time(NULL));
    auto endT = rand() % 24;
    endT = 0;
    for(int i = -1; i < endT; i++){
        std::for_each(builders.begin(), builders.end(), [](Builder &ep){ep.calculatedBid();});
        winningBuilder = &(*std::max_element(builders.begin(), builders.end(),
                                             [](const Builder &a, const Builder &b) {
                                                 return a.currBid < b.currBid; // Compare currBid values
                                             }));
        maxBid = winningBuilder -> currBid;
    }

}