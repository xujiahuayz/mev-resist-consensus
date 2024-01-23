//
// Created by Aaryan Gulia on 19/01/2024.
//

#ifndef PBS_C_AUCTION_H
#define PBS_C_AUCTION_H
#include "vector"
#include "blockchain_env/Builder.h"

class Auction {

public:
    typedef std::vector<Builder> BuilderMap;
    BuilderMap builders;
    double maxBid = 0;
    Builder* winningBuilder;
    double auctionTime = 0;

    Auction(BuilderMap &aBuilders);

    void runAuction();
};


#endif //PBS_C_AUCTION_H
