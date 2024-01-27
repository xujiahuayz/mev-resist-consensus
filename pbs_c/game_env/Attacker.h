#ifndef PBS_C_ATTACKER_H
#define PBS_C_ATTACKER_H

#include "blockchain_env/Transaction.h"
#include <vector>
#include "blockchain_env/Block.h"

class TransactionFactory;
class BuilderFactory;
class Attacker {
private:
    TransactionFactory& transactionFactory;
    BuilderFactory& builderFactory;
    std::vector<std::shared_ptr<Transaction>> targetTransactions;
    std::vector<std::shared_ptr<Transaction>> frontTransactions;
    std::vector<std::shared_ptr<Transaction>> backTransactions;
    int attackCounter = 0;

public:
    Attacker(TransactionFactory& transactionFactory, BuilderFactory& builderFactory);
    void attack(int idHint);
    void results(std::vector<std::shared_ptr<Block>> blocks);
    void removeFailedAttack(std::shared_ptr<Block> block);
};

#endif //PBS_C_ATTACKER_H