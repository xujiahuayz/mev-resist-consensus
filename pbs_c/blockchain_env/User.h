#include "factory/TransactionFactory.h"
#include <memory>

class Users {
private:
    TransactionFactory& transactionFactory;

public:
    Users(TransactionFactory& transactionFactory);

    void createTransaction(double gas, double mev, int id);
};