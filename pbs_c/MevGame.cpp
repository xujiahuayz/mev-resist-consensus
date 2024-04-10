#include "blockchain_env/Blockchain.h"

int main() {
    int numBuilders =4;
    int numConnection = numBuilders/2;
    int depth = 0;
    int numSimulations = 100;
    int builderCharacteristic = 80;
    int chainLength = 500;
    int numTransactions = 100;
    double mevTransPercentage = 1;
    int maxBlockSize = 10;

    NodeFactory nodeFactory;
    nodeFactory.createBuilderNode(1,5,1,depth,numSimulations);
    nodeFactory.createBuilderNode(2,5,1,depth,numSimulations);
    nodeFactory.createBuilderNode(3,5,1,depth,numSimulations);
    nodeFactory.createBuilderNode(4,5,1,depth,numSimulations);
    nodeFactory.createBuilderNode(5,5,1,depth,numSimulations);

    nodeFactory.createAttackerBuilderNode(10,5,1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(30,5,1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(50,5,1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(70,5,1,depth,numSimulations);
    nodeFactory.createAttackerBuilderNode(90,5,1,depth,numSimulations);

//    nodeFactory.createAttackerBuilderNode(110,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(130,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(150,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(170,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(190,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(210,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(230,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(250,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(270,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(290,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(310,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(330,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(350,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(370,5,1,depth,numSimulations);
//    nodeFactory.createAttackerBuilderNode(390,5,1,depth,numSimulations);

    nodeFactory.createProposerNode(6,5,1);
    nodeFactory.createProposerNode(7,5,1);
    nodeFactory.createProposerNode(8,5,1);
    nodeFactory.createProposerNode(9,5,1);

    nodeFactory.createNode(11,5,1);
    nodeFactory.createNode(12,5,1);

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
