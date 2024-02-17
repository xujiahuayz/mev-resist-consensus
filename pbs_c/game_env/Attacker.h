#ifndef PBS_C_ATTACKER_H
#define PBS_C_ATTACKER_H

#include "blockchain_env/Builder.h"
#include <vector>

class NodeFactory;
class Attacker : virtual public Node{
protected:
    NodeFactory& nodeFactory;
    std::vector<std::shared_ptr<Transaction>> frontTransactions;
    std::vector<std::shared_ptr<Transaction>> backTransactions;
    int attackCounter = 0;

public:
    std::vector<std::shared_ptr<Transaction>> targetTransactions;
    Attacker(size_t aId, int aConnections, double aCharacteristic, NodeFactory& nodeFactory);
    void attack();
    void clearAttacks();
    void removeFailedAttack(std::shared_ptr<Block> block);
};

#endif //PBS_C_ATTACKER_H