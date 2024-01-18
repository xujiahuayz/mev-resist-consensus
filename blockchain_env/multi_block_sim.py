import random
from scipy.stats import pareto


class BiddingGame:
    def __init__(
        self,
        lambda_g: float,
        lambda_m: float,
        alpha: float,
        num_simulations: int,
        timesteps: int,
        nmev_builders: int,
        mev_builders:int
    ):
        self.lambda_g = lambda_g
        self.lambda_m = lambda_m
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.timesteps = timesteps
        self.nmev_builders = nmev_builders
        self.mev_builders = mev_builders
        self.max_bids:list[list[float]] = []

    def simulate(self):
        results:list[bool] = []
        self.max_bids.append([])
        b_char:list[float] = pareto.rvs(self.alpha, size = self.mev_builders + self.nmev_builders)
        for _ in range(self.num_simulations):
            # These are random changes to builder characteristics in each block. As of now the distribution of the change 
            # is a pure assumption without any empirical research.
            b_char = [char + char * random.normalvariate(0,1)/10 for char in b_char]
            builders:list[Builder] = [Builder(self.lambda_g, self.lambda_m, char) for char in b_char[:self.nmev_builders]]
            builders += [Builder(self.lambda_g, 0, char) for char in b_char[-self.mev_builders:]]
            auction: Auction = Auction(builders, self.timesteps)
            results.append(auction.run())
            self.max_bids[-1].append(auction.max_bid)

        return results


class Builder:
    def __init__(self, gas_scaling: float, 
                 mev_scaling: float, 
                 characteristic: float
                 ):
        self.gas_scaling = gas_scaling
        self.charateristic = characteristic
        self.mev_scaling = mev_scaling
        self.bid:float = 0

    def calculate_bid(self, W_t: int):
        self.bid = (
            (self.gas_scaling + self.mev_scaling) * (self.charateristic)
            + self.gas_scaling * W_t
            + self.mev_scaling * W_t
        )

    def update_bid(self, W_t: int):
        # I have added in the assumptuion that W_t for both MEV and Gas will not be independent
        # as if number of transactions in the mempool are high, the gas fee will be more and so
        # will the MEV opportunities. The assumption here is both W_t's are equal
        self.bid += self.gas_scaling * W_t + self.mev_scaling * W_t


class Auction:
    def __init__(self, builders:list[Builder],
                timesteps: int):
        self.builders = builders
        self.timesteps = timesteps
        self.max_bid:float = 0

    def run(self):
        # This generated Wiener process, the specification of which doesn't 
        # change the result of the simulations (the scale does)
        W_t: int = random.randint(-1, 1) / 10

        [builder.calculate_bid(W_t) for builder in self.builders]

        # The proposer can end the auction at any time in the block time
        end_time: int = random.randint(0, self.timesteps)

        for _ in range(end_time):
            W_t = random.randint(-1, 1) / 10
            [builder.update_bid(W_t) for builder in self.builders]
        
        max_builder = max(self.builders, key = lambda builder: builder.bid)
        self.max_bid = max_builder.bid

        return not(max_builder.mev_scaling)
