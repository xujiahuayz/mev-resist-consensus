#include "blockchain_env/Blockchain.h"
int main() {
    int numBuilders = 5;
    Blockchain blockchain(200,numBuilders);
    blockchain.startChain();
    blockchain.printBlockStats();
    blockchain.saveBlockData();
    return 0;
}
