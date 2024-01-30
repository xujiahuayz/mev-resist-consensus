#ifndef PBS_C_BUILDERFACTORY_H
#define PBS_C_BUILDERFACTORY_H
#include "blockchain_env/Builder.h"
#include <vector>
#include <memory>

class BuilderFactory {
public:

    std::shared_ptr<Builder> createBuilder(int bId, double bCharacteristic);
    std::shared_ptr<Builder> createBuilder(int bId);
    std::shared_ptr<Builder> createBuilder(int bId, double bCharacteristic, double bConnections, double bDepth, double bNumSim);

    // Add a builder to the list
    void addBuilder(const std::shared_ptr<Builder>& builder);

    // Remove a builder from the list
    void removeBuilder(const std::shared_ptr<Builder>& builder);

    std::vector<std::shared_ptr<Builder>> builders;
    void assignNeighbours(int numConnections);
    void addTransactionsToBuilder(TransactionFactory& transactionFactory);
    void propagateTransactions();
    void clearMempools(std::shared_ptr<Transaction> transaction);
};


#endif //PBS_C_BUILDERFACTORY_H