//
// Created by Aaryan Gulia on 19/01/2024.
//
#include <boost/random/lognormal_distribution.hpp>
#include <boost/random/normal_distribution.hpp>
#include <boost/random.hpp>
#include <chrono>
#include <random>

double genRandNormal(double mean,double std){
    auto seed = static_cast<unsigned>(
            std::chrono::high_resolution_clock::now().time_since_epoch().count());
    std::random_device rd;
    seed ^= rd();
    boost::random::mt19937 rng(seed);
    boost::random::normal_distribution<> normalDist(mean, std);
    double rand = normalDist(rng) * 100;
    return rand;
}

double genRandLognormal(double logMean, double logStd){
    auto seed = static_cast<unsigned>(
            std::chrono::high_resolution_clock::now().time_since_epoch().count());
    std::random_device rd;
    seed ^= rd();
    boost::random::mt19937 rng(seed);

    boost::random::lognormal_distribution<> lognormalDist(logMean,logStd);
    double rand = lognormalDist(rng);
    return rand;
}

// Initialize a random number generator
static std::mt19937 rng(std::random_device{}());

int genRandInt(int min, int max) {
    std::uniform_int_distribution<int> dist(min, max);
    return dist(rng);
}