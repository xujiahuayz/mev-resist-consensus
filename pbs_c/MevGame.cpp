#include "blockchain_env/Blockchain.h"

int main() {
    int numBuilders =4;
    int numConnection = numBuilders/2;
    int depth = 0;
    int numSimulations = 100;
    int builderCharacteristic = 80;
    int chainLength = 5000;
    int numTransactions = 100;
    double mevTransPercentage = 1;
    int maxBlockSize = 10;

    NodeFactory nodeFactory;
//    float ch = 0.1;
//    for(int i = 10; i < 999;){
//        if(ch>.95){
//            ch = 0.95;
//        }
//        nodeFactory.createProposerAttackerBuilderNode(i,5,ch,depth,numSimulations);
//        ch+=0.02;
//        i+=20;
//    }

    nodeFactory.createProposerBuilderNode(1,100,.1,depth,numSimulations);
    nodeFactory.createProposerBuilderNode(2,100,.1,depth,numSimulations);
    nodeFactory.createProposerBuilderNode(3,100,.1,depth,numSimulations);
    nodeFactory.createProposerBuilderNode(4,100,.1,depth,numSimulations);
    nodeFactory.createProposerBuilderNode(5,100,.1,depth,numSimulations);

    nodeFactory.createProposerAttackerBuilderNode(10,100,.1,depth,numSimulations);
    nodeFactory.createProposerAttackerBuilderNode(30,100,.1,depth,numSimulations);
    nodeFactory.createProposerAttackerBuilderNode(50,100,.1,depth,numSimulations);
    nodeFactory.createProposerAttackerBuilderNode(70,100,.1,depth,numSimulations);
    nodeFactory.createProposerAttackerBuilderNode(90,100,.1,depth,numSimulations);

    for(int i = 1000; i < 1400; i++){
        nodeFactory.createNode(i,5,.1);
    }


    nodeFactory.assignNeighbours();

    Blockchain blockchain(chainLength,nodeFactory);
    blockchain.startChainPbs();
    blockchain.saveTrasactionData("pbsTransactions.csv", blockchain.pbsBlocks);
//    blockchain.saveTrasactionData("posTransactions.csv", blockchain.posBlocks);
    blockchain.saveBlockData("pbsBlocks.csv", blockchain.pbsBlocks);
//    blockchain.saveBlockData("posBlocks.csv", blockchain.posBlocks);
//    blockchain.saveComparisonData("comparison.csv");
    return 0;
}
