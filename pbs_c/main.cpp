#include "blockchain_env/Blockchain.h"
int main() {
    int numBuilders = 5;
    Blockchain blockchain(1000,numBuilders);
    blockchain.startChain();
    blockchain.printBlockStats();
    blockchain.saveBlockData();
    return 0;
}
