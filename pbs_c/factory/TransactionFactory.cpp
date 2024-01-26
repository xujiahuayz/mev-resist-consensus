#include <random>
#include "TransactionFactory.h"

TransactionFactory::TransactionFactory(int numTransactions, double mevPercentage)
    : numTransactions(numTransactions), mevPercentage(mevPercentage){
    createTransactions(0.5);
}

void TransactionFactory::createTransactions(int idHint) {
    int id = idHint*10000;
    std::uniform_real_distribution<double> distribution(0.0, 100.0);
    for (int i = transactions.size(); i < numTransactions; i++) {
        double gasFee = distribution(randomGenerator.rng);
        double mev = distribution(randomGenerator.rng) < mevPercentage ? distribution(randomGenerator.rng) : 0.0;
        transactions.push_back(Transaction(gasFee, mev, id++));
    }
}
void TransactionFactory::createTransactions(Transaction transaction){
    transactions.push_back(transaction);
}

void TransactionFactory::deleteTransaction(int index) {
    if (index >= 0 && index < transactions.size()) {
        transactions.erase(transactions.begin() + index);
    }
}

double TransactionFactory::totalGasFees() const {
    double total = 0.0;
    for (const auto& transaction : transactions) {
        total += transaction.gas;
    }
    return total;
}

double TransactionFactory::totalMEV() const {
    double total = 0.0;
    for (const auto& transaction : transactions) {
        total += transaction.mev;
    }
    return total;
}