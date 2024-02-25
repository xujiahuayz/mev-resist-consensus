//
// Created by Aaryan Gulia on 29/01/2024.
//

#ifndef PBS_C_NODEFACTORY_H
#define PBS_C_NODEFACTORY_H
#include "game_env/AttackerBuilder.h"
#include <vector>
#include <memory>
#include <set>

class NodeFactory {
public:
    std::vector<std::shared_ptr<Node>> nodes;
    std::vector<std::shared_ptr<Builder>> builders;
    std::vector<std::shared_ptr<Attacker>> attackers;
    std::vector<std::shared_ptr<Proposer>> proposers;

    void createBuilderNode(int bId, int bConnections,double bCharacteristic, double bDepth, double bNumSim);
    void createAttackerNode(size_t aId, int aConnections, double aCharacteristic);
    void createAttackerBuilderNode(int baId, int baConnections, double baCharacteristic, double baDepth, double baNumSim);
    void createProposerNode(int pId, int pConnections, double pCharacteristic);
    void createNode(int nId, int connections, double characteristic);
    void addTransactionToNodes(std::shared_ptr<Transaction> transaction);
    void assignNeighbours();
    void propagateTransactions();
    void clearMempools(std::shared_ptr<Transaction> transaction);
};

#endif //PBS_C_NODEFACTORY_H