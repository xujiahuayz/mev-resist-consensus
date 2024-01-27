#include <vector>
#include "blockchain_env/Transaction.h"

class TransactionFactory {
private:
    int numTransactions;
    double mevPercentage;

public:
    std::vector<Transaction> transactions;
    TransactionFactory(int numTransactions, double mevPercentage);
    void createTransactions(int idHint);
    void createTransactions(int idHint, double gas, double mev);
    void createTransactions(Transaction transaction);
    void deleteTransaction(std::shared_ptr<Transaction> transaction);
    double totalGasFees() const;
    double totalMEV() const;
};