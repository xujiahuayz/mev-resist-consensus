//
// Created by Aaryan Gulia on 29/01/2024.
//

#ifndef PBS_C_NODEFACTORY_H
#define PBS_C_NODEFACTORY_H
#include "game_env/ProposerBuilder.h"
#include <vector>
#include <memory>
#include <set>
#include <unordered_set>

class NodeFactory {
public:
    std::vector<std::shared_ptr<Node>> nodes;
    std::vector<std::shared_ptr<Builder>> builders;
    std::vector<std::shared_ptr<Attacker>> attackers;
    std::vector<std::shared_ptr<Proposer>> proposers;

    std::vector<std::shared_ptr<Transaction>> allTransactionsVec;
    std::unordered_set<std::shared_ptr<Transaction>> allTransactionsSet;

    void createBuilderNode(int bId, int bConnections,double bCharacteristic, double bDepth, double bNumSim);
    void createAttackerNode(size_t aId, int aConnections, double aCharacteristic);
    void createAttackerBuilderNode(int baId, int baConnections, double baCharacteristic, double baDepth, double baNumSim);
    void createProposerNode(int pId, int pConnections, double pCharacteristic);
    void createProposerBuilderNode(int pbId, int pbConnections, double pbCharacteristic, double pbDepth, double pbNumSim);
    void createProposerAttackerBuilderNode(int paId, int paConnections, double paCharacteristic, double paDepth, double paNumSim);
    void createNode(int nId, int connections, double characteristic);
    void addTransactionToNodes(std::shared_ptr<Transaction> transaction);
    void assignNeighbours();
    void propagateTransactions();
    void clearMempools(std::shared_ptr<Transaction> transaction);
};

#endif //PBS_C_NODEFACTORY_H