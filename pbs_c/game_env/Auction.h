//
// Created by Aaryan Gulia on 19/01/2024.
//

#ifndef PBS_C_AUCTION_H
#define PBS_C_AUCTION_H
#include "vector"
#include "factory/nodeFactory.h"

class Auction {

public:
    std::shared_ptr<Block> auctionBlock;
    NodeFactory& nodeFactory;
    double auctionTime = 0;

    Auction(NodeFactory& nodeFactory):nodeFactory(nodeFactory){}

    void runAuction();
};


#endif //PBS_C_AUCTION_H
