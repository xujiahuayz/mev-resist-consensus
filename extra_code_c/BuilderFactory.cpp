#include "BuilderFactory.h"
#include <algorithm> // for std::shuffle

std::shared_ptr<Builder> BuilderFactory::createBuilder(int bId, double bCharacteristic) {
    std::shared_ptr<Builder> newBuilder = std::make_shared<Builder>(bId, bCharacteristic);
    return newBuilder;
}

std::shared_ptr<Builder> BuilderFactory::createBuilder(int bId) {
    std::shared_ptr<Builder> newBuilder = std::make_shared<Builder>(bId);
    return newBuilder;
}
std::shared_ptr<Builder> BuilderFactory::createBuilder(int bId, double bCharacteristic, double bConnections, double bDepth, double bNumSim) {
    std::shared_ptr<Builder> newBuilder = std::make_shared<Builder>(bId, bCharacteristic, bConnections, bDepth, bNumSim);
    return newBuilder;
}

void BuilderFactory::addBuilder(const std::shared_ptr<Builder>& builder) {
    builders.push_back(builder);
}

void BuilderFactory::removeBuilder(const std::shared_ptr<Builder>& builder) {
    builders.erase(std::remove(builders.begin(), builders.end(), builder), builders.end());
}

void BuilderFactory::assignNeighbours(int numConnections) {
    for (auto& builder1 : builders) {
        std::vector<std::shared_ptr<Builder>> otherBuilders(builders);
        otherBuilders.erase(std::remove_if(otherBuilders.begin(),
                                           otherBuilders.end(),
                                           [&](const std::shared_ptr<Builder>& builder2)
                                           {return builder1 == builder2 ||
                                                   std::find(builder1->adjBuilders.begin(),builder1->adjBuilders.end(), builder2) !=builder1->adjBuilders.end();}
        ),otherBuilders.end());
        std::shuffle(otherBuilders.begin(), otherBuilders.end(), randomGenerator.rng);
        int i = 0;
        while(i<otherBuilders.size() && builder1->adjBuilders.size() < builder1->connections){
            if (otherBuilders[i]->adjBuilders.size() < otherBuilders[i]->connections){
                builder1->adjBuilders.push_back(otherBuilders[i]);
                otherBuilders[i++]->adjBuilders.push_back(builder1);
            }
            else{
                i++;
            }
        }
    }
}

void BuilderFactory::addTransactionsToBuilder(TransactionFactory& transactionFactory) {
    for (auto& transaction : transactionFactory.transactions) {
        if ( randomGenerator.genRandInt(0, 100) < 25){
            continue;
        }
        bool isInMempool = false;
        for (auto& builder : builders) {
            isInMempool = std::find_if(builder->mempool.begin(), builder->mempool.end(),
                                       [&](const std::shared_ptr<Transaction>& t) { return t->id == transaction.id; }) != builder->mempool.end();
            if (isInMempool) {
                break;
            }
        }
        if (!isInMempool) {
            int randomIndex = randomGenerator.genRandInt(0, builders.size() - 1);
            std::shared_ptr<Transaction> t = std::make_shared<Transaction>(transaction);
            builders[randomIndex]->mempool.push_back(t);
        }
    }
}

void BuilderFactory::propagateTransactions() {
    for (auto& builder : builders) {
        for (auto& neighbor : builder->adjBuilders) {
            for (auto& transaction : neighbor->mempool) {
                bool isInMempool = std::find_if(builder->mempool.begin(), builder->mempool.end(),
                                                [&](const std::shared_ptr<Transaction>& t) { return t->id == transaction->id; }) != builder->mempool.end();
                if (!isInMempool) {
                    int randomIndex = randomGenerator.genRandInt(0, 100);
                    if (randomIndex < 50){
                        builder->mempool.push_back(transaction);
                    }
                }
            }
        }
    }
}
void BuilderFactory::clearMempools(std::shared_ptr<Transaction> transaction) {
    for (auto& builder : builders) {
        builder->mempool.erase(std::remove_if(builder->mempool.begin(), builder->mempool.end(),
                                              [&](const std::shared_ptr<Transaction>& t) { return t->id == transaction->id; }),
                               builder->mempool.end());
    }
}