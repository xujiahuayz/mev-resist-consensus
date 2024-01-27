#include "blockchain_env/Blockchain.h"
int main() {
    int numBuilders = 4;
    Blockchain blockchain(500,numBuilders);
    blockchain.startChain();
    blockchain.printBlockStats();
    blockchain.saveBlockData();
    blockchain.saveToCSV("transactions.csv");
    return 0;
}
