import heapq
import numpy as np
import time
import copy

# 0 - hot_food
# 1 - sandwitch
# 2 - drink
# 3 - cash

mu = 30
num_of_server = []
total_sim_time = 5400

group_size = [1, 2, 3, 4]
group_size_probabilities = [0.5, 0.3, 0.1, 0.1]

routing = [[0, 2, 3], [1, 2, 3], [2, 3]]
routes_probabilities = [0.80, 0.15, 0.05]

act = [[20, 40], [5, 15], [0, 0], [5, 10]]
st = [[50, 120], [60, 180], [0, 0], [5, 20]]

expansion_possibilities = [[1, 1, 5, 2], [1, 1, 5, 3], [1, 2, 5, 2], [1, 2, 5, 3], [2, 1, 5, 2], [2, 1, 5, 3], [2, 2, 5, 2], [2, 2, 5, 3]]


class States:
    def __init__(self):
        self.total_num_of_group = 0
        self.num_of_customers_in_system = 0
        self.is_new_group = {}
        self.queue = [[[]], [[]], [[]], []]
        self.num_of_server = num_of_server

        for i in range(self.num_of_server[3]):
            self.queue[3].append([])

        self.avg_route_delay = [0.0, 0.0, 0.0]
        self.avg_queue_delay = [0.0, 0.0, 0.0, 0.0]
        self.avg_queue_length = [0.0, 0.0, 0.0, 0.0]
        self.total_customer_served_by_this_counter = [0, 0, 0, 0]

        self.max_customer_in_the_system = 0
        self.max_route_delay = [0.0, 0.0, 0.0]
        self.max_queue_delay = [0.0, 0.0, 0.0, 0.0]
        self.max_queue_length = [0.0, 0.0, 0.0, 0.0]
        self.total_customer_served_by_this_route = [0, 0, 0]

        self.time_last_event = 0
        self.overall_avg_delay = 0
        self.avg_customer_in_system = 0

    def update(self, event):
        time_since_last_event = event.event_time - self.time_last_event
        self.time_last_event = event.event_time

        for i in range(4):
            num_of_customer_in_queue = 0
            for j in range(len(self.queue[i])):
                num_of_customer_in_queue += len(self.queue[i][j])
                self.max_queue_length[i] = max(self.max_queue_length[i], len(self.queue[i][j]))
            if len(self.queue[i]) > 0:
                self.avg_queue_length[i] += round(num_of_customer_in_queue / len(self.queue[i]), 3) * time_since_last_event

        self.avg_customer_in_system += time_since_last_event * self.num_of_customers_in_system
        self.max_customer_in_the_system = max(self.max_customer_in_the_system, self.num_of_customers_in_system)

    def finish(self, sim):
        for i in range(4):
            self.max_queue_delay[i] = round(self.max_queue_delay[i] / 60, 3)
            self.avg_queue_length[i] /= sim.now()
            if self.total_customer_served_by_this_counter[i] > 0:
                self.avg_queue_delay[i] = round(self.avg_queue_delay[i] / (60 * self.total_customer_served_by_this_counter[i]), 3)

        for i in range(3):
            if self.total_customer_served_by_this_route[i] > 0:
                self.avg_route_delay[i] = round(self.avg_route_delay[i] / (60 * self.total_customer_served_by_this_route[i]), 3)
            self.overall_avg_delay += (routes_probabilities[i] * self.avg_route_delay[i])
            self.max_route_delay[i] = round(self.max_route_delay[i] / 60, 3)

        self.avg_customer_in_system = round(self.avg_customer_in_system / sim.now(), 3)

    def report(self):
        print("Customer served by each counter  ", self.total_customer_served_by_this_counter)
        print("Average delays in queue: ", self.avg_queue_length)
        print("Max delays in the queue: ", self.max_queue_delay)

        print("Average queue length: ", self.avg_queue_length)
        print("Max queue length: ", self.max_queue_length)

        print("Average delay for each route: ", self.avg_route_delay)
        print("Max delay for each route: ", self.max_route_delay)

        print("Overall delay: ", self.overall_avg_delay)
        print("Maximum customer at any time instance: ", self.max_customer_in_the_system)
        print("Average customer: ", self.avg_customer_in_system)
        print("Total customer served: ", self.total_customer_served_by_this_counter[3])
        print("\n\n\n")


class Event:
    def __init__(self, sim):
        self.eventType = None
        self.sim = sim
        self.event_time = None

    def process(self):
        raise Exception('Unimplemented process method for the event!')

    def __repr__(self):
        return self.eventType

    def __lt__(self, other):
        return True


class StartEvent(Event):
    def __init__(self, event_time, sim):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'START'
        self.sim = sim

    def process(self):
        self.sim.states.total_num_of_group += 1
        arrival_time = self.sim.now() + np.random.exponential(mu)
        num_of_people_in_group = np.random.choice(group_size, p=group_size_probabilities)

        for i in range(num_of_people_in_group):
            route_index = np.random.choice([0, 1, 2], p=routes_probabilities)
            self.sim.states.total_customer_served_by_this_route[route_index] += 1
            self.sim.schedule_event(ArrivalEvent(arrival_time, self.sim, self.sim.states.total_num_of_group, route_index, 0, 0))

        self.sim.schedule_event(ExitEvent(total_sim_time, self.sim))


class ExitEvent(Event):
    def __init__(self, event_time, sim):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self):
        None


class ArrivalEvent(Event):
    def __init__(self, event_time, sim, group_no, route_idx, counter_idx, queue_idx):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'ARRIVAL'
        self.sim = sim
        self.group_no = group_no
        self.route_idx = route_idx
        self.counter_idx = counter_idx
        self.queue_idx = queue_idx

    def process(self):
        current_counter = routing[self.route_idx][self.counter_idx]

        if self.counter_idx == 0:
            self.sim.states.num_of_customers_in_system += 1

        if self.counter_idx == 0 and self.group_no not in self.sim.states.is_new_group:
            self.sim.states.is_new_group[self.group_no] = True
            self.sim.states.total_num_of_group += 1
            arrival_time = self.sim.now() + np.random.exponential(mu)
            num_of_people_in_group = np.random.choice(group_size, p=group_size_probabilities)

            for i in range(num_of_people_in_group):
                route_index = np.random.choice([0, 1, 2], p=routes_probabilities)
                self.sim.states.total_customer_served_by_this_route[route_index] += 1
                self.sim.schedule_event(ArrivalEvent(arrival_time, self.sim, self.sim.states.total_num_of_group, route_index, 0, 0))

        if self.sim.states.num_of_server[current_counter] == 0:
            min_queue_length = np.inf
            for i in range(len(self.sim.states.queue[current_counter])):
                if len(self.sim.states.queue[current_counter][i]) < min_queue_length:
                    min_queue_length = len(self.sim.states.queue[current_counter][i])
                    self.queue_idx = i
            self.sim.states.queue[current_counter][self.queue_idx].append(self)
        else:
            queue_idx = 0
            service_time = 0

            if current_counter != 2:
                self.sim.states.num_of_server[current_counter] -= 1

            if current_counter != 3:
                service_time = np.random.uniform(st[current_counter][0], st[current_counter][1])
            else:
                for i in routing[self.route_idx]:
                    service_time += np.random.uniform(act[i][0], act[i][1])
                queue_idx = self.sim.states.num_of_server[current_counter]

            self.sim.states.total_customer_served_by_this_counter[current_counter] += 1
            self.sim.schedule_event(DepartureEvent(self.event_time + service_time, self.sim, self.group_no, self.route_idx, self.counter_idx, queue_idx))


class DepartureEvent(Event):
    def __init__(self, event_time, sim, group_no, route_idx, counter_idx, queue_idx):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'DEPARTURE'
        self.sim = sim
        self.group_no = group_no
        self.route_idx = route_idx
        self.counter_idx = counter_idx
        self.queue_idx = queue_idx

    def process(self):
        current_counter = routing[self.route_idx][self.counter_idx]

        if len(self.sim.states.queue[current_counter][self.queue_idx]) == 0:
            self.sim.states.num_of_server[current_counter] += 1
        else:
            service_time = 0

            if current_counter != 3:
                service_time = np.random.uniform(st[current_counter][0], st[current_counter][1])
            else:
                for i in routing[self.route_idx]:
                    service_time += np.random.uniform(act[i][0], act[i][1])

            front_event = self.sim.states.queue[current_counter][self.queue_idx].pop(0)
            delay = self.event_time - front_event.event_time

            self.sim.states.avg_route_delay[front_event.route_idx] += delay
            self.sim.states.max_route_delay[front_event.route_idx] = max(self.sim.states.max_route_delay[front_event.route_idx], delay)

            if current_counter != 2:
                self.sim.states.avg_queue_delay[current_counter] += delay
                self.sim.states.max_queue_delay[current_counter] = max(self.sim.states.max_queue_delay[current_counter], delay)

            self.sim.states.total_customer_served_by_this_counter[current_counter] += 1
            self.sim.schedule_event(DepartureEvent(self.event_time + service_time, self.sim, front_event.group_no, front_event.route_idx, front_event.counter_idx, front_event.queue_idx))

        if self.counter_idx < len(routing[self.route_idx]) - 1:
            self.sim.schedule_event(ArrivalEvent(self.event_time, self.sim, self.group_no, self.route_idx, self.counter_idx + 1, 0))
        else:
            self.sim.states.num_of_customers_in_system -= 1


class Simulator:
    def __init__(self):
        self.eventQ = []
        self.simulator_clock = 0
        self.states = States()

    def initialize(self):
        self.simulator_clock = 0
        self.schedule_event(StartEvent(0, self))

    def now(self):
        return self.simulator_clock

    def schedule_event(self, event):
        heapq.heappush(self.eventQ, (event.event_time, event))

    def run(self):
        self.initialize()
        while len(self.eventQ) > 0:
            current_time, event = heapq.heappop(self.eventQ)
            if event.eventType == 'EXIT':
                break
            if self.states is not None:
                self.states.update(event)
            self.simulator_clock = event.event_time
            event.process()
        self.states.finish(self)
        self.states.report()


def init(idx):
    global num_of_server, st, act
    num_of_server = expansion_possibilities[idx]
    temp_st = copy.deepcopy(st)
    temp_act = copy.deepcopy(act)

    for i in range(2):
        for j in range(2):
            st[i][j] = st[i][j] / num_of_server[i]
            act[i][j] = act[i][j] / num_of_server[i]

    st = copy.deepcopy(temp_st)
    act = copy.deepcopy(temp_act)


if __name__ == "__main__":
    for i in range(8):
        print("---------------RUN---------------", i)
        print("Expansion Posibilitis: ", expansion_possibilities[i])
        init(i)
        seed = 101
        np.random.seed(seed)
        sim = Simulator()
        sim.run()
