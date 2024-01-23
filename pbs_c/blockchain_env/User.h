//
// Created by Aaryan Gulia on 18/01/2024.
//

#ifndef PBS_C_USER_H
#define PBS_C_USER_H

#include "Transaction.h"
#include "vector"

class User{
public:
    std::vector<Transaction> transactions;
    void makeTransaction(int tId, double tAmount);
};


#endif //PBS_C_USER_H
