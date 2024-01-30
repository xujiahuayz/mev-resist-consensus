#include "blockchain_env/Blockchain.h"

int main() {
    int numBuilders =4;
    int numConnection = numBuilders/2;
    int depth = 0;
    int numSimulations = 100;
    int builderCharacteristic = 80;
    int chainLength = 500;
    int numTransactions = 100;
    double mevTransPercentage = 0.5;
    int maxBlockSize = 10;

    NodeFactory nodeFactory;
    nodeFactory.createBuilderNode(1, 2,0.1,depth,numSimulations);
    nodeFactory.createBuilderNode(2, 2,0.1,depth,numSimulations);
    nodeFactory.createBuilderNode(3, 2,0.1,depth,numSimulations);
    nodeFactory.createBuilderNode(4,2,0.1,depth,numSimulations);

    TransactionFactory transactionFactory(numTransactions, 50);

    nodeFactory.createAttackerNode(1,2,0.1);


    nodeFactory.assignNeighbours();
    for(auto& transaction : transactionFactory.transactions){
        nodeFactory.addTransactionToNodes(std::make_shared<Transaction>(transaction));
    }
    Blockchain blockchain(chainLength,nodeFactory);
    blockchain.startChain();
    blockchain.saveToCSV("transactions.csv");
    return 0;
}
