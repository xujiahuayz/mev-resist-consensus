//
// Created by Aaryan Gulia on 18/01/2024.
//

#ifndef PBS_C_TRANSACTION_H
#define PBS_C_TRANSACTION_H
#include "Random.h"

class Transaction {
public:
    double amount,gas,mev;
    int id;

    Transaction(double GAS, double MEV): gas(GAS), mev(MEV){
        genId();
    }
    Transaction(double GAS, double MEV, int tId): gas(GAS), mev(MEV), id(tId){
    }
    void genId(){
        id = randomGenerator.genRandInt(0,100000);}
};


#endif //PBS_C_TRANSACTION_H
