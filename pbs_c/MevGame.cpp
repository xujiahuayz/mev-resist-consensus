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
    nodeFactory.createBuilderNode(4, 2,0.1,depth,numSimulations);
    nodeFactory.createBuilderNode(5, 2,0.8,depth,numSimulations);

    nodeFactory.createAttackerBuilderNode(10, 2,0.1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(30, 2,0.1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(50, 2,0.1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(70, 2,0.1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(90, 2,0.8,depth,numSimulations);

    nodeFactory.createProposerNode(6, 2,0.1);
    nodeFactory.createProposerNode(7, 2,0.1);
    nodeFactory.createProposerNode(8, 2,0.1);
    nodeFactory.createProposerNode(9, 2,0.1);

    nodeFactory.createNode(11, 2,0.1);
    nodeFactory.createNode(12, 2,0.1);

    TransactionFactory transactionFactory(numTransactions, 50);


    nodeFactory.assignNeighbours();
    for(auto& transaction : transactionFactory.transactions){
        nodeFactory.addTransactionToNodes(std::make_shared<Transaction>(transaction));
    }
    Blockchain blockchain(chainLength,nodeFactory);
    blockchain.startChainPosPbs();
    blockchain.saveTrasactionData("pbsTransactions.csv", blockchain.pbsBlocks);
    blockchain.saveTrasactionData("posTransactions.csv", blockchain.posBlocks);
    blockchain.saveBlockData("pbsBlocks.csv", blockchain.pbsBlocks);
    blockchain.saveBlockData("posBlocks.csv", blockchain.posBlocks);
    blockchain.saveComparisonData("comparison.csv");
    return 0;
}
