#include "Attacker.h"
#include "factory/NodeFactory.h"

Attacker::Attacker(size_t aId, int aConnections, double aCharacteristic, NodeFactory& nodeFactory)
        : Node(aId,aConnections,aCharacteristic),nodeFactory(nodeFactory) {}

void Attacker::attack() {
    for (auto& builder : adjNodes) {
        Builder* b = dynamic_cast<Builder*>(builder.get());
        if(b)
        {for (auto &transaction: builder->mempool) {
                if (transaction->mev > (transaction->gas) * 3 &&
                    find(targetTransactions.begin(), targetTransactions.end(), transaction) ==
                    targetTransactions.end()) {
                    targetTransactions.push_back(transaction);
                    frontTransactions.push_back(std::make_shared<Transaction>(
                            Transaction(transaction->gas + 0.01, 0, id * 1000 + attackCounter)));
                    backTransactions.push_back(std::make_shared<Transaction>(
                            Transaction(transaction->gas - 0.01, 0, (id * 1000 + attackCounter++) * -1)));
                    builder->mempool.insert(frontTransactions.back());
                    builder->mempool.insert(backTransactions.back());
                }
            }
        }
    }
}
void Attacker::clearAttacks(){
    if(targetTransactions.size() != 0){
        for(int i = 0; i < frontTransactions.size(); i++){
            nodeFactory.clearMempools(frontTransactions[i]);
            nodeFactory.clearMempools(backTransactions[i]);
        }
        frontTransactions.clear();
        backTransactions.clear();
        targetTransactions.clear();
    }
}

void Attacker::removeFailedAttack(std::shared_ptr<Block> block) {
    int counter = 0;
    for (auto& targetTransaction : targetTransactions) {
        if(targetTransaction == nullptr){
            continue;
        }
        auto trans = std::find_if(block->transactions.begin(), block->transactions.end(),
                                  [&](std::shared_ptr<Transaction> t){return t->id == targetTransaction->id;});
        // Check if the target transaction is not in the transaction factory
        if (trans != block->transactions.end()) {
            nodeFactory.clearMempools(frontTransactions[counter]);
            nodeFactory.clearMempools(backTransactions[counter]);
        }
        counter++;
    }
    for(int i = 0; i < frontTransactions.size(); i++){
        auto trans1 = std::find_if(block->transactions.begin(), block->transactions.end(),
                                   [&](std::shared_ptr<Transaction> t){return t->id == frontTransactions[i]->id;});
        auto trans2 = std::find_if(block->transactions.begin(), block->transactions.end(),
                                   [&](std::shared_ptr<Transaction> t){return t->id == backTransactions[i]->id;});
        if(trans1 != block->transactions.end() || trans2 != block->transactions.end()){
            nodeFactory.clearMempools(frontTransactions[i]);
            nodeFactory.clearMempools(backTransactions[i]);
        }
    }
}