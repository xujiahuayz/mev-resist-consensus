#include "blockchain_env/Blockchain.h"
int main() {
    int numBuilders = 4;
    Blockchain blockchain(100,numBuilders);
    blockchain.startChain();
    blockchain.printBlockStats();
    blockchain.saveBlockData();
    return 0;
}
