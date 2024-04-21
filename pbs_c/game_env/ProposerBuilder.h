//
// Created by Aaryan Gulia on 21/04/2024.
//

#ifndef PBS_C_PROPOSERBUILDER_H
#define PBS_C_PROPOSERBUILDER_H
#include "AttackerBuilder.h"
class ProposerBuilder: public Proposer, public Builder{
public:
    ProposerBuilder(int pId, int pConnections, double pCharacteristic, double pDepth, double pNumSim,NodeFactory& nodeFactory):
    Proposer(pId,pConnections,pCharacteristic, nodeFactory), Builder(pId,pConnections,pCharacteristic,pDepth,pNumSim),
    Node(pId,pConnections,pCharacteristic){};

    void runAuction() override;



};


#endif //PBS_C_PROPOSERBUILDER_H
