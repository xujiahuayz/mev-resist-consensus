#ifndef PBS_C_NODE_H
#define PBS_C_NODE_H

#include <vector>
#include <memory>
#include "Transaction.h"
#include "set"

class Builder; // Forward declaration

class Node {
public:
    int id;
    int connections;
    double characteristic;
    std::vector<std::shared_ptr<Node>> adjNodes;
    std::set<std::shared_ptr<Transaction>> mempool;

    Node(int id, int connections, double characteristic) :id(id), connections(connections), characteristic(characteristic) {}

    virtual ~Node(){}
};

#endif //PBS_C_NODE_H