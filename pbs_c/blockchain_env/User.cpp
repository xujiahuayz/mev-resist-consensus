#include "User.h"

Users::Users(TransactionFactory& transactionFactory) : transactionFactory(transactionFactory) {}

void Users::createTransaction(double gas, double mev, int id) {
    std::shared_ptr<Transaction> newTransaction = std::make_shared<Transaction>(gas, mev, id);
    transactionFactory.createTransactions(*newTransaction);
}