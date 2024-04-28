//
// Created by Aaryan Gulia on 25/04/2024.
//

#include "RandomNumberData.h"

RandomNumberData* RandomNumberData::instance = nullptr;

RandomNumberData::RandomNumberData() {
    std::ifstream file("../random_numbers.txt");
    if (!file) {
        std::cerr << "Unable to open file" << std::endl;
        return;
    }

    std::cout<< "Reading random numbers from file" << std::endl;

    std::string num_str;
    randomNumbers.reserve(100000000);
    while (std::getline(file, num_str)) {
        float number = std::stof(num_str);
        randomNumbers.push_back(number);
    }
}

RandomNumberData* RandomNumberData::getInstance() {
    if (instance == nullptr) {
        instance = new RandomNumberData();
    }
    return instance;
}

std::vector<float>& RandomNumberData::getRandomNumbers() {
    return randomNumbers;
}
