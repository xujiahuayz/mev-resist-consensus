#include "Attacker.h"

#ifndef PBS_C_ATTACKERBUILDER_H
#define PBS_C_ATTACKERBUILDER_H


class AttackerBuilder : public Attacker, public Builder{
public:
    AttackerBuilder(size_t abId, int abConnections, double abCharacteristic, double abDepth, double abNumSim, NodeFactory& nodeFactory);
    void buildBlock(int maxBlockSize) override;



};


#endif //PBS_C_ATTACKERBUILDER_H
