//
// Created by Aaryan Gulia on 18/01/2024.
//

#ifndef PBS_C_TRANSACTION_H
#define PBS_C_TRANSACTION_H


class Transaction {
public:
    double amount,gas,mev;
    int id;

    Transaction(int tId, double tAmount): id(tId), amount(tAmount),gas(tAmount/100),mev(tAmount/100){
    }
};


#endif //PBS_C_TRANSACTION_H
