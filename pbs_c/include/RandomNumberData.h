//
// Created by Aaryan Gulia on 25/04/2024.
//

#ifndef PBS_C_RANDOMNUMBERDATA_H
#define PBS_C_RANDOMNUMBERDATA_H

#include <iostream>
#include <fstream>
#include <vector>

class RandomNumberData {
private:
    std::vector<float> randomNumbers;
    static RandomNumberData* instance;

    // Private constructor so that no objects can be created.
    RandomNumberData();
public:
    // Static access method
    static RandomNumberData* getInstance();

    std::vector<float>& getRandomNumbers();
};

// Initialize pointer to zero so that it can be initialized in the first call to getInstance
extern RandomNumberData* instance;


#endif //PBS_C_RANDOMNUMBERDATA_H
