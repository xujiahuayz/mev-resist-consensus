#include "blockchain_env/Blockchain.h"
#include "fstream"


void saveData(const std::string& filename, std::vector<double> blockValues, std::vector<double> blockBids) {
    std::ofstream file(filename);
    for (int i = 0; i < blockValues.size(); i++) {
        file << i+2 <<"," << blockValues[i] << "," << blockBids[i] << std::endl;
    }
    file.close();
}

void saveBlockchainData(const std::string& filename, const std::vector<std::shared_ptr<Block>>& blocks) {
    std::ofstream file(filename);


}

int main() {
    int depth = 0;
    int numSimulations = 100;
    int builderCharacteristic = 80;
    int chainLength = 2000;
    int numTransactions = 100;
    int numMaxBuilders = 20;

    std::vector<double> blockValues;
    std::vector<double> blockBids;

    for (int i = 2; i <= numMaxBuilders; i++) {
        double blockValue = 0;
        double blockBid = 0;
        for(int simnum = 0; simnum < 3; simnum++){
            NodeFactory nodeFactory;
            int connections = i > 5 ? 5 : i - 1;
            for (int j = 1; j <= i; j++) {
                nodeFactory.createProposerAttackerBuilderNode(j, connections, 1, depth, numSimulations);
            }


            nodeFactory.createNode(11, 5, 1);
            nodeFactory.createNode(12, 5, 1);

            TransactionFactory transactionFactory(numTransactions, 50);
            nodeFactory.assignNeighbours();
            for (auto &transaction: transactionFactory.transactions) {
                nodeFactory.addTransactionToNodes(std::make_shared<Transaction>(transaction));
            }
            Blockchain blockchain(chainLength, nodeFactory);
            blockchain.startChainPosPbs();
            for (auto &block: blockchain.pbsBlocks) {
                blockValue += block->blockValue;
                blockBid += block->bid;
            }
        }
        blockValues.push_back(blockValue / 3);
        blockBids.push_back(blockBid / 3);
    }
    saveData("num_builder_sim.csv", blockValues, blockBids);
    return 0;
}
