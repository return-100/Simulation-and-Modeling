"""
The task is to simulate an M/M/k system with a single queue.
Complete the skeleton code and produce results for three experiments.
The study is mainly to show various results of a queue against its ro parameter.
ro is defined as the ratio of arrival rate vs service rate.
For the sake of comparison, while plotting results from simulation, also produce the analytical results.
"""

import heapq
import random
import matplotlib.pyplot as plt

inf = 10000000000
total_people = 80000


class Params:
    def __init__(self, lambd, mu, k):
        self.lambd = lambd  # interarrival rate
        self.mu = mu  # service rate
        self.k = k


class States:
    def __init__(self):
        self.queue = []
        self.people_in_queue = 0
        self.total_area_in_queue = 0.0
        self.served = 0

        self.available_server = 0
        self.last_event_time = 0
        self.total_delay = 0.0
        self.total_served_time = 0.0

        self.util = 0.0
        self.avgQdelay = 0.0
        self.avgQlength = 0.0

    def update(self, sim, event):
        busy_server = sim.params.k - self.available_server
        last_event_duration = event.eventTime - self.last_event_time
        self.total_area_in_queue += self.people_in_queue * last_event_duration
        self.last_event_time = event.eventTime
        self.total_served_time += last_event_duration * (busy_server / sim.params.k)

    def finish(self, sim):
        self.avgQdelay = self.total_delay / self.served
        self.avgQlength = self.total_area_in_queue / sim.now()
        self.util = self.total_served_time / sim.now()

    def printResults(self, sim):
        # DO NOT CHANGE THESE LINES
        print('MMk Results: lambda = %lf, mu = %lf, k = %d' % (sim.params.lambd, sim.params.mu, sim.params.k))
        print('MMk Total customer served: %d' % self.served)
        print('MMk Average queue length: %lf' % self.avgQlength)
        print('MMk Average customer delay in queue: %lf' % self.avgQdelay)
        print('MMk Time-average server utility: %lf\n' % self.util)

    def getResults(self, sim):
        return self.avgQlength, self.avgQdelay, self.util


class Event:
    def __init__(self, sim):
        self.eventType = None
        self.sim = sim
        self.eventTime = None

    def process(self, sim):
        raise Exception('Unimplemented process method for the event!')

    def __repr__(self):
        return self.eventType


class StartEvent(Event):
    def __init__(self, eventTime, sim):
        super().__init__(sim)
        self.eventTime = eventTime
        self.eventType = 'START'
        self.sim = sim

    def process(self, sim):
        sim.states.served += 1
        exp = random.expovariate(sim.params.lambd)
        self.sim.scheduleEvent(ArrivalEvent(self.eventTime + exp, self.sim))
        self.sim.scheduleEvent(ExitEvent(inf, self.sim))


class ExitEvent(Event):
    def __init__(self, eventTime, sim):
        super().__init__(sim)
        self.eventTime = eventTime
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self, sim):
        None


class ArrivalEvent(Event):
    def __init__(self, eventTime, sim):
        super().__init__(sim)
        self.eventTime = eventTime
        self.eventType = 'ARRIVAL'
        self.sim = sim

    def process(self, sim):
        if sim.states.served < total_people:
            sim.states.served += 1
            exp = random.expovariate(sim.params.lambd)
            self.sim.scheduleEvent(ArrivalEvent(sim.now() + exp, self.sim))

        if sim.states.available_server == 0:
            sim.states.people_in_queue += 1
            sim.states.queue.append(sim.now())
        else:
            sim.states.available_server -= 1
            exp = random.expovariate(sim.params.mu)
            sim.scheduleEvent(DepartureEvent(sim.now() + exp, sim))


class DepartureEvent(Event):
    def __init__(self, eventTime, sim):
        super().__init__(sim)
        self.eventTime = eventTime
        self.eventType = 'DEPARTURE'
        self.sim = sim

    def process(self, sim):
        if sim.states.people_in_queue == 0:
            sim.states.available_server += 1
        else:
            sim.states.people_in_queue -= 1
            sim.states.total_delay += (sim.now() - sim.states.queue[0])
            sim.states.queue.pop(0)
            expo = random.expovariate(sim.params.mu)
            sim.scheduleEvent(DepartureEvent(sim.now() + expo, sim))


class Simulator:
    def __init__(self, seed):
        self.eventQ = []
        self.simclock = 0
        self.seed = seed
        self.params = None
        self.states = None

    def initialize(self):
        self.simclock = 0
        self.scheduleEvent(StartEvent(0, self))

    def configure(self, params, states):
        self.params = params
        self.states = states
        self.states.available_server = self.params.k

    def now(self):
        return self.simclock

    def scheduleEvent(self, event):
        heapq.heappush(self.eventQ, (event.eventTime, event))

    def run(self):
        random.seed(self.seed)
        self.initialize()

        while len(self.eventQ) > 0:
            time, event = heapq.heappop(self.eventQ)

            if event.eventType == 'EXIT':
                break

            if self.states is not None:
                self.states.update(self, event)

            # print(event.eventTime, 'Event', event)
            self.simclock = event.eventTime
            event.process(self)

        self.states.finish(self)

    def printResults(self):
        self.states.printResults(self)

    def getResults(self):
        return self.states.getResults(self)

    def print_analytical_results(self):
        avgQlength = (self.params.lambd * self.params.lambd) / (self.params.mu * (self.params.mu - self.params.lambd))
        avgQdelay = self.params.lambd / (self.params.mu * (self.params.mu - self.params.lambd))
        util = self.params.lambd / self.params.mu
        print('\nAnalytical Results: lambda = %lf, mu = %lf, k = %d' % (self.params.lambd, self.params.mu, self.params.k))
        print('Analytical Average queue length: %lf' % avgQlength)
        print('Analytical Average customer delay in queue: %lf' % avgQdelay)
        print('Analytical Time-average server utility: %lf' % util)


def experiment3():
    seed = 110
    lambd = 5.0 / 60
    mu = 8.0 / 60

    avglength = []
    avgdelay = []
    util = []
    server = []

    for k in range(1, 5, 1):
        sim = Simulator(seed)
        sim.configure(Params(lambd, mu, k), States())
        sim.run()
        sim.printResults()

        length, delay, utl = sim.getResults()
        avglength.append(length)
        avgdelay.append(delay)
        util.append(utl)
        server.append(k)

    plt.figure(1)
    plt.subplot(311)
    plt.plot(server, avglength)
    plt.xlabel('Server (k)')
    plt.ylabel('Avg Q length')

    plt.subplot(312)
    plt.plot(server, avgdelay)
    plt.xlabel('Server (k)')
    plt.ylabel('Avg Q delay (sec)')

    plt.subplot(313)
    plt.plot(server, util)
    plt.xlabel('Server (k)')
    plt.ylabel('Util')

    plt.show()


def main():
    experiment3()


if __name__ == "__main__":
    main()
