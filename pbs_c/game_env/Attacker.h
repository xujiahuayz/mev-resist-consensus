#ifndef PBS_C_ATTACKER_H
#define PBS_C_ATTACKER_H

#include "blockchain_env/Transaction.h"
#include <vector>
#include "blockchain_env/Block.h"

class TransactionFactory;
class Attacker {
private:
    TransactionFactory& transactionFactory;
    std::vector<std::shared_ptr<Transaction>> targetTransactions;
    std::vector<std::shared_ptr<Transaction>> frontTransactions;
    std::vector<std::shared_ptr<Transaction>> backTransactions;

public:
    Attacker(TransactionFactory& transactionFactory);
    void attack(int idHint);
    void results(std::vector<std::shared_ptr<Block>> blocks);
};

#endif //PBS_C_ATTACKER_H