#include "NodeFactory.h"
#include <unordered_set>


void NodeFactory::createBuilderNode(int bId, int bConnections, double bCharacteristic, double bDepth, double bNumSim) {
    std::shared_ptr<Builder> newBuilder = std::make_shared<Builder>(bId, bCharacteristic, bConnections, bDepth, bNumSim);
    builders.push_back(newBuilder);
    nodes.push_back(newBuilder);
}

void NodeFactory::createAttackerNode(size_t aId, int aConnections, double aCharacteristic) {
    std::shared_ptr<Attacker> newAttacker = std::make_shared<Attacker>(aId, aConnections, aCharacteristic,*this);
    attackers.push_back(newAttacker);
    nodes.push_back(newAttacker);
}

void NodeFactory::createAttackerBuilderNode(int baId, int baConnections, double baCharacteristic, double baDepth, double baNumSim) {
    std::shared_ptr<AttackerBuilder> newAttackerBuilder = std::make_shared<AttackerBuilder>(baId, baConnections, baCharacteristic, baDepth, baNumSim);
    builders.push_back(newAttackerBuilder);
    nodes.push_back(newAttackerBuilder);
}

void NodeFactory::createProposerNode(int pId, int pConnections, double pCharacteristic) {
    std::shared_ptr<Proposer> newProposer = std::make_shared<Proposer>(pId, pConnections, pCharacteristic, *this);
    proposers.push_back(newProposer);
    nodes.push_back(newProposer);
}

void NodeFactory::createProposerBuilderNode(int pbId, int pbConnections, double pbCharacteristic, double pbDepth,
                                            double pbNumSim) {
    std::shared_ptr<ProposerBuilder> newProposerBuilder = std::make_shared<ProposerBuilder>(pbId, pbConnections, pbCharacteristic, pbDepth, pbNumSim, *this);
    proposers.push_back(newProposerBuilder);
    builders.push_back(newProposerBuilder);
    nodes.push_back(newProposerBuilder);
}

void NodeFactory::createProposerAttackerBuilderNode(int paId, int paConnections, double paCharacteristic, double paDepth,
                                                    double paNumSim) {
    std::shared_ptr<ProposerAttackerBuilder> newProposerAttackerBuilder = std::make_shared<ProposerAttackerBuilder>(paId, paConnections, paCharacteristic, paDepth, paNumSim, *this);
    proposers.push_back(newProposerAttackerBuilder);
    builders.push_back(newProposerAttackerBuilder);
    nodes.push_back(newProposerAttackerBuilder);
}

void NodeFactory::createNode(int nId, int connections, double characteristic) {
    std::shared_ptr<Node> newNode = std::make_shared<Node>(nId,connections,characteristic);
    nodes.push_back(newNode);
}

void NodeFactory::addTransactionToNodes(std::shared_ptr<Transaction> transaction) {
    bool isInMempool = false;
    for (auto& node : nodes) {
        isInMempool = node->mempool.find(transaction) != node->mempool.end();
        if (isInMempool) {
            break;
        }
    }
    if (!isInMempool) {
        int randomIndex = randomGenerator.genRandInt(0, nodes.size() - 1);
        nodes[randomIndex]->mempool.insert(transaction);
    }
}

void NodeFactory::assignNeighbours() {
    for (auto& node1 : nodes) {
        std::vector<std::shared_ptr<Node>> otherNodes(nodes);
        otherNodes.erase(std::remove_if(otherNodes.begin(),
                                        otherNodes.end(),
                                        [&](const std::shared_ptr<Node>& node2)
                                        {return node1 == node2 ||
                                                std::find(node1->adjNodes.begin(),node1->adjNodes.end(), node2) !=node1->adjNodes.end();}
        ),otherNodes.end());
        std::shuffle(otherNodes.begin(), otherNodes.end(), randomGenerator.rng);
        int i = 0;
        while(i<otherNodes.size() && node1->adjNodes.size() < node1->connections){
            if (otherNodes[i]->adjNodes.size() < otherNodes[i]->connections){
                node1->adjNodes.push_back(otherNodes[i]);
                otherNodes[i++]->adjNodes.push_back(node1);
            }
            else{
                i++;
            }
        }
    }
}

void NodeFactory::propagateTransactions() {
    for (auto& node : nodes) {
        std::unordered_set<std::shared_ptr<Transaction>> nodeMempool(node->mempool.begin(), node->mempool.end());
        for (auto& neighbor : node->adjNodes) {
            for (auto& transaction : neighbor->mempool) {
                if (nodeMempool.find(transaction) == nodeMempool.end()) {
                    int randomIndex = randomGenerator.genRandInt(0, 100);
                    if (randomIndex <= 100*neighbor->characteristic){
                        node->mempool.insert(transaction);

                    }
                }
            }
        }
    }
}

void NodeFactory::clearMempools(std::shared_ptr<Transaction> transaction) {
    for (auto& node : nodes) {
        node->mempool.erase(transaction);
    }
}