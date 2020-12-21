import heapq
import math
import numpy as np

sim_time = 8
sim_length = 1

num_of_stations = 0
num_of_machines_in_each_station = []
mu = 0.0
num_of_job_types = 0
job_probabilities = []
num_of_stations_for_each_job = []
routing_for_each_job = []
mean_service_time_for_each_job = []

class States:
    def __init__(self):
        self.queue = []
        self.avg_queue_delay = []
        self.area_in_queue = []
        self.avg_queue_delay = []
        self.avg_num_in_queue = []
        self.total_customer_served_by_each_station = []

        for i in range(num_of_stations):
            self.queue.append([])
            self.avg_queue_delay.append(0)
            self.total_customer_served_by_each_station.append(0)
            self.area_in_queue.append(0)
            self.avg_queue_delay.append(0)
            self.avg_num_in_queue.append(0)

        self.num_of_jobs_in_the_system = 0
        self.num_of_server = num_of_machines_in_each_station

        self.job_cnt = []
        self.avg_job_delay = []
        for i in range(num_of_job_types):
            self.job_cnt.append(0)
            self.avg_job_delay.append(0)

        self.area_number_job = 0
        self.time_since_last_event = 0.0
        self.overall_avg_delay = 0.0
        self.avg_number_of_jobs = 0

    def update(self, event):
        time_since_last_event = event.event_time - self.time_since_last_event
        self.time_since_last_event = event.event_time

        self.avg_number_of_jobs += self.num_of_jobs_in_the_system * time_since_last_event

        for i in range(num_of_stations):
            self.area_in_queue[i] += len(self.queue[i]) * time_since_last_event

    def finish(self, sim):
        self.overall_avg_delay = 0

        for i in range(num_of_stations):
            if self.total_customer_served_by_each_station[i] != 0:
                self.avg_queue_delay[i] /= self.total_customer_served_by_each_station[i]
            self.avg_num_in_queue[i] = self.area_in_queue[i] / sim.now()

        for i in range(num_of_job_types):
            if self.job_cnt[i] != 0:
                self.avg_job_delay[i] /= self.job_cnt[i]
                self.overall_avg_delay += job_probabilities[i] * self.avg_job_delay[i]

        self.avg_number_of_jobs /= sim.now()

    def report(self, sim):
        None

class Event:
    def __init__(self, sim):
        self.eventType = None
        self.sim = sim
        self.event_time = None

    def process(self, sim):
        raise Exception('Unimplemented process method for the event!')

    def __repr__(self):
        return self.eventType


class StartEvent(Event):
    def __init__(self, event_time, sim):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'START'
        self.sim = sim

    def process(self, sim):
        arrival_time = self.event_time + np.random.exponential(mu)
        job_type = np.random.choice(list(range(0, num_of_job_types)), p=job_probabilities)
        self.sim.schedule_event(ArrivalEvent(arrival_time, self.sim, job_type, 0))
        self.sim.schedule_event(ExitEvent(sim_time * sim_length, self.sim))


class ExitEvent(Event):
    def __init__(self, event_time, sim):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'EXIT'
        self.sim = sim

    def process(self, sim):
        None


class ArrivalEvent(Event):
    def __init__(self, event_time, sim, job_type, station_idx):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'ARRIVAL'
        self.sim = sim
        self.job_type = job_type
        self.station_idx = station_idx

    def process(self, sim):
        current_station = routing_for_each_job[self.job_type][self.station_idx]

        if sim.states.num_of_server[current_station] > 0:
            sim.states.num_of_server[current_station] -= 1
            mean_time = mean_service_time_for_each_job[self.job_type][self.station_idx]
            erlang = 2 * np.random.exponential(mean_time / 2)
            sim.schedule_event(DepartureEvent(self.sim.now() + erlang, self.sim, self.job_type, self.station_idx))
        else:
            sim.states.queue[current_station].append(self)

        if self.station_idx == 0:
            self.sim.states.num_of_jobs_in_the_system += 1
            self.sim.states.job_cnt[self.job_type] += 1
            arrival_time = self.event_time + np.random.exponential(mu)
            job_type = np.random.choice(list(range(0, num_of_job_types)), p=job_probabilities)
            self.sim.schedule_event(ArrivalEvent(arrival_time, self.sim, job_type, 0))


class DepartureEvent(Event):
    def __init__(self, event_time, sim, job_type, station_idx):
        super().__init__(sim)
        self.event_time = event_time
        self.eventType = 'DEPARTURE'
        self.sim = sim
        self.job_type = job_type
        self.station_idx = station_idx

    def process(self, sim):
        current_station = routing_for_each_job[self.job_type][self.station_idx]

        if len(self.sim.states.queue[current_station]) > 0:
            front_event = self.sim.states.queue[current_station].pop(0)
            delay = self.sim.now() - front_event.event_time

            self.sim.states.avg_queue_delay[current_station] += delay
            self.sim.states.avg_job_delay[front_event.job_type] += delay

            mean_time = mean_service_time_for_each_job[front_event.job_type][front_event.station_idx]
            erlang = 2 * np.random.exponential(mean_time / 2)
            sim.schedule_event(DepartureEvent(self.sim.now() + erlang, self.sim, front_event.job_type, front_event.station_idx))
        else:
            self.sim.states.num_of_server[current_station] += 1

        self.sim.states.total_customer_served_by_each_station[current_station] += 1

        if self.station_idx < num_of_stations_for_each_job[self.job_type] - 1:
            self.sim.schedule_event(ArrivalEvent(self.sim.now(), self.sim, self.job_type, self.station_idx + 1))
        else:
            self.sim.states.current_jobs_in_system -= 1


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
            time, event = heapq.heappop(self.eventQ)
            if event.eventType == 'EXIT':
                break

            if self.states is not None:
                self.states.update(event)

            self.simulator_clock = event.event_time
            event.process(self)

        return self.states.finish(self)


def read_input():
    global num_of_stations, num_of_machines_in_each_station, mu, num_of_job_types, job_probabilities
    global num_of_stations_for_each_job, routing_for_each_job, mean_service_time_for_each_job

    file = open("input.txt", "r")
    line = file.readline()
    num_of_stations = int(line[0])

    line = file.readline().split()
    for i in range(len(line)):
        num_of_machines_in_each_station.append(int(line[i]))

    line = file.readline().split()
    mu = float(line[0])

    line = file.readline().split()
    num_of_job_types = int(line[0])

    line = file.readline().split()
    for i in range(len(line)):
        job_probabilities.append(float(line[i]))

    line = file.readline().split()
    for i in range(len(line)):
        num_of_stations_for_each_job.append(int(line[i]))

    for i in range(num_of_job_types):
        line = file.readline().split()
        routing = []
        for j in range(len(line)):
            routing.append(int(line[j]))
        routing_for_each_job.append(routing)
        line = file.readline().split()
        mean_service_time = []
        for j in range(len(line)):
            mean_service_time.append(float(line[j]))
        mean_service_time_for_each_job.append(mean_service_time)


if __name__ == "__main__":
    read_input()

    avg_job_delay = None
    avg_num_in_queue = None
    overall_avg_delay = None
    avg_num_of_jobs = None
    avg_queue_delay = None

    for i in range(30):
        sim = Simulator()
        sim.run()

        for j in range(num_of_job_types):
            avg_job_delay[j] += (sim.states.avg_job_delay[j] / 30)

        for j in range(num_of_stations):
            avg_queue_delay[j] += (sim.states.avg_queue_delay[j] / 30)
            avg_num_in_queue[j] += (sim.states.avg_num_in_queue[j] / 30)

        overall_avg_delay += (sim.states.overall_avg_delay / 30)
        avg_num_of_jobs += (sim.states.avg_number_of_jobs / 30)

    print("Average queue delay for each job: ", avg_queue_delay)
    print("Average total delay in each job: ", avg_job_delay)
    print("Average number of jobs: ", avg_num_of_jobs)
    print("Overall average delay: ", overall_avg_delay)
