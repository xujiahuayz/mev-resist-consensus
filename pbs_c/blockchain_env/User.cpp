//
// Created by Aaryan Gulia on 18/01/2024.
//

#include "User.h"
#include "Transaction.h"

void User::makeTransaction(int tId, double tAmount){
    transactions.push_back(Transaction(tId,tAmount));
}