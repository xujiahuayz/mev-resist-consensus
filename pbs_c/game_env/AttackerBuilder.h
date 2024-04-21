#include "Proposer.h"

#ifndef PBS_C_ATTACKERBUILDER_H
#define PBS_C_ATTACKERBUILDER_H


class AttackerBuilder : virtual public Builder{
public:
    AttackerBuilder(size_t abId, int abConnections, double abCharacteristic, double abDepth, double abNumSim);
    void buildBlock(int maxBlockSize) override;



};


#endif //PBS_C_ATTACKERBUILDER_H
