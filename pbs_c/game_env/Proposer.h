//
// Created by Aaryan Gulia on 24/02/2024.
//

#ifndef PBS_C_PROPOSER_H
#define PBS_C_PROPOSER_H
#include "Attacker.h"

class NodeFactory;
class Proposer: public Node{
public:
    std::shared_ptr<Block> proposedBlock;
    std::map<int,float> currBids;
    std::map<int,float> currBlockValues;
    std::map<int,float> currCharactaristics;
    NodeFactory& nodeFactory;
    Proposer(size_t pId, int pConnections, double pCharacteristic, NodeFactory& nodeFactory);
    void propose(std::shared_ptr<Block>& block);
    void runAuction();

};


#endif //PBS_C_PROPOSER_H
