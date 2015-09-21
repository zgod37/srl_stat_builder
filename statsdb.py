"""
SRL Stat + DB access class
"""

import sqlite3
import api
import datetime as dt
import srlplayer

DB_NAME = 'srlstatistics.db'

class SRLStats:

    def __init__(self):
        self._race_table = ""
        self._result_table = ""

    def create_tables(self, game):
        """
        Creates 2 tables (race and result)
        Tables have one-to-many relationship
        Each SRL ID has one race row, and 2 or more result rows
        """

        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            #set table names
            self._race_table = game
            self._result_table = game+'results'

            c.execute("DROP TABLE IF EXISTS "+self._race_table)
            c.execute("CREATE TABLE "+self._race_table+" (date text, id int, game text, goal text, numentrants int, timestamp int)")

            c.execute("DROP TABLE IF EXISTS "+self._result_table)
            c.execute("CREATE TABLE "+self._result_table+ " (id int, player text, place int, time int, comment text)")

            conn.commit()
        except sqlite3.Error as e:
            print('Error creating tables! ', e)
        finally:
            conn.close()

    def add_to_tables(self, races):
        """
        Add list of races to tables
        """

        #first build rows for query
        race_rows = []
        result_rows = []
        for race in races:
            race_rows.append(self.build_race_row(race))
            result_rows.extend(self.build_result_rows(race['results']))
        
        #query database
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            c.executemany("INSERT INTO "+self._race_table+" VALUES (?,?,?,?,?,?)", race_rows)
            c.executemany("INSERT INTO "+self._result_table+" VALUES (?,?,?,?,?)", result_rows)

            conn.commit()
        except sqlite3.Error as e:
            print('Error adding to tables: ', e)
        finally:
            conn.close()

    def remove_from_tables(self, race_id):
        """
        Remove race from tables
        """

        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
        
            tables = (self._race_table, self._result_table)

            for table in tables:
                c.execute("DELETE FROM "+table+" WHERE id=?",(race_id,))

            conn.commit()
        except sqlite3.Error as e:
            print("Error removing from tables: ", e)
        finally:
            conn.close()

    def remove_many_from_tables(self, race_ids):
        """
        Remove many races from tables
        """

        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
        
            tables = (self._race_table, self._result_table)

            for table in tables:
                c.execute("DELETE FROM "+table+" WHERE id IN (%s)" % ','.join('?'*len(race_ids)), race_ids)

            conn.commit()
        except sqlite3.Error as e:
            print("Error removing from tables: ", e)
        finally:
            conn.close()

    def build_race_row(self, race):
        """
        build sql-ready row for race table
        """
        return((api.get_datetime(race), race['id'], race['game']['name'], race['goal'], race['numentrants'], race['date']))

    def build_result_rows(self, results):
        """
        build sql-ready rows for result table
        """
        result_rows = []
        for result in results:
            result_rows.append((result['race'], result['player'], result['place'], 
                result['time'], result['message']))
        return result_rows

    def build_player_records(self, race_ids):
        """
        Build Player records from given list of race ids
        Accesses results table for desired races
        Uses 2 enclosed helper functions
        Return list of newly created Players
        """

        players = []

        # #####################
        # HELPER FUNCTIONS

        def get_player(name):
            for player in players:
                if name == player.get_name():
                    return(player)

        def update_stats(player, place, time):
            player.increment_joins()
            
            if place >= 9998:
                player.increment_quits()
            else:
                player.add_ranking(place)

            if time > 0:
                player.add_time(time)
            
        # ######################

        rows = self.get_from_rows_by_id(self._result_table, race_ids, '*')

        for row in rows:
            name = row['player'].lower()
            player = get_player(name)

            if not player:
                player = srlplayer.Player(name)
                players.append(player)

            update_stats(player, row['place'], row['time'])


        return players

    def build_race_stats(self, race_ids):
        """
        Build stats pertaining to race ids
        Return list of stat rows (stat_lbl, stat_val)
        """
        
        race_rows = self.get_from_rows_by_id(self._race_table, race_ids, 'numentrants')
        
        #get entrant stats
        most_entrants = 0
        total_entrants = 0
        for row in race_rows:
            total_entrants += row['numentrants']
            if row['numentrants'] > most_entrants:
                most_entrants = row['numentrants']
        

        
        #get quit rate stats
        result_rows = self.get_from_rows_by_id(self._result_table, race_ids, 'id, place')

        #use id to keep track of race
        current_id = result_rows[0]['id']
        quits = 0
        joins = 0
        quit_rates = []
        for row in result_rows:

            #if new id, compute quit rate for prev race
            if row['id'] != current_id:
                quit_rates.append((quits/joins)*100)
                current_id = row['id']
                joins = 0
                quits = 0

            joins += 1
            if row['place'] >= 9998:
                quits += 1

        #get last race
        quit_rates.append((quits/joins)*100)

        #build race stats
        race_stats = []
        race_stats.append(('Total Races:', len(race_ids)))
        race_stats.append(('Most Entrants:', most_entrants))
        race_stats.append(('Average Entrants:', round(total_entrants/len(race_ids), 2)))
        race_stats.append(('Average Quit Rate:', round(sum(quit_rates)/len(race_ids),2)))
        race_stats.append(('Highest Quit Rate:', round(max(quit_rates), 2)))

        print(race_stats)
        return race_stats
        
    def get_from_rows_by_id(self, table, race_ids, col):
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("SELECT "+col+" FROM "+table+" WHERE id IN (%s)" % ','.join('?'*len(race_ids)), race_ids)

            rows = c.fetchall()

        except sqlite3.Error as e:
            print('sqlite error: ', e)
        finally:
            conn.close()

        return rows