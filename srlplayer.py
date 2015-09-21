"""
SRL Player Record

Object for containing a record for a SRL Player
"""

import collections

class Player:

    def __init__(self, name):
        self._name = name
        self._joins = 0
        self._quits = 0
        self._times = []
        self._rankings = collections.defaultdict(int)

    def increment_joins(self):
        self._joins += 1
    
    def increment_quits(self):
        self._quits += 1

    def add_time(self, time):
        self._times.append(time)

    def add_ranking(self, rank):
        self._rankings[rank] += 1

    def get_average_time(self):

        if len(self._times) == 0:
            return "DNF"

        total = 0
        for time in self._times:
            total += time
        return total/len(self._times)

    def get_name(self):
        return self._name

    def get_joins(self):
        return self._joins

    def get_quits(self):
        return self._quits

    def get_ranking(self, rank):
        return self._rankings[rank]

    def get_win_rate(self):
        return round((self._rankings[1]/self._joins)*100, 2)

    def get_top3_rate(self):
        top3 = self._rankings[1] + self._rankings[2] + self._rankings[3]
        return round((top3/self._joins)*100, 2)

    def get_quit_rate(self):
        return round((self._quits/self._joins)*100, 2)