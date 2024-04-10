cmake_minimum_required(VERSION 3.26)
project(pbs_c)

set(CMAKE_CXX_STANDARD 23)

# Find external dependencies
FIND_PACKAGE( Boost 1.40 COMPONENTS program_options REQUIRED )

set(SOURCE_DIRS)
file(GLOB_RECURSE SOURCE_DIRS **.cpp)

file(GLOB_RECURSE REMOVE_CMAKE "cmake-build-debug/*")
list(REMOVE_ITEM SOURCE_DIRS ${REMOVE_CMAKE})

add_executable(pbs_c main.cpp
        blockchain_env/User.cpp
        blockchain_env/Builder.cpp
        game_env/Auction.h
        game_env/Auction.cpp
        blockchain_env/Blockchain.h
        blockchain_env/Blockchain.cpp
        include/Random.h
        include/Random.cpp
        factory/TransactionFactory.h
        factory/TransactionFactory.cpp
        blockchain_env/Block.h
        game_env/Attacker.h
        game_env/Attacker.cpp
        blockchain_env/Node.h
        factory/NodeFactory.h
        factory/NodeFactory.cpp
        game_env/AttackerBuilder.h
        game_env/AttackerBuilder.cpp
        game_env/Proposer.h
        game_env/Proposer.cpp
)


INCLUDE_DIRECTORIES( ${Boost_INCLUDE_DIR} ${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/include )

TARGET_LINK_LIBRARIES( pbs_c LINK_PUBLIC ${Boost_LIBRARIES} )