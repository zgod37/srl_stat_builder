"""
GUI for SRL Stat Analyzer

Handles all of the GUI Code

** TODO **

* Implement all the weekly race features
    * display weekday name in date column of race_tree
    * filterweekly -> grab race with most number of entrants
    * checkweekly -> check for missed weeks and/or false positives
    * possibly use background color to highlight?
    * prompt user for the weekday that race is held on
* Fix statdb to get stats for querys over 999
* polish GUI for main window
    * GUI IDEA make a simple/advanced search, use button to hide/show frame for advanced search related-fields - can use grid_remove
* revisit overall structure or prgm and integration of classes
    * redo import of statsdb so that class is initialized when imported
    * look into SRLStatsApp -> inherits from ttk.Frame? probably not good
    * "from tkinter import *" is probably bad and should be re-factored

* KNOWN BUG: creating multiple race editors by performing API search
            while a race editor is already on screen causes the tables
            to be overwritten by the new search.
"""

from tkinter import *
from tkinter import ttk

import api
import statsdb as statdb
import datetime
import math
import random
import os
import csv

class SRLStatsApp(ttk.Frame):
    
    def __init__(self, master=None):
        #create widgets and stuff
        self.stats = statdb.SRLStats()
        ttk.Frame.__init__(self, master)
        self.create_main_window()    
    
    def create_main_window2(self):
        """
        Create Search window with simple+advanced search
        use a checkbox to show/hide the advanced search fields
        """

        t = Toplevel(self)
        upper_frame = ttk.Frame(root)

        main_lbl = ttk.Label(upper_frame, text='Enter Game Info', font=('Helvetica',16), justify="center")

        game = StringVar()
        game_lbl = ttk.Label(upper_frame, text='enter game abbrev:')
        game_entry = ttk.Entry(upper_frame, width=20, textvariable=game)

        goal = StringVar()
        goal_lbl = ttk.Label(upper_frame, text='goal')
        goal_entry = ttk.Entry(upper_frame, width=20, textvariable=goal)

        adv_btn = ttk.Button(text="Advanced »", command=lambda: self.toggle_advanced(lower_frame, adv_btn, True))
        sep = ttk.Separator(upper_frame, orient=HORIZONTAL)

        lower_frame = ttk.Frame(root)

        startdate = StringVar()
        start_lbl = ttk.Label(lower_frame, text='enter startdate:')
        start_entry = ttk.Entry(lower_frame, width=20, textvariable=startdate)

        enddate = StringVar()
        end_lbl = ttk.Label(lower_frame, text='enter enddate:')
        end_entry = ttk.Entry(lower_frame, width=20, textvariable=enddate)

        weekday = StringVar()
        weekday_lbl = ttk.Label(lower_frame, text='weekday:')
        weekday_box = ttk.Combobox(lower_frame, values=('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat','Sun'), textvariable=weekday)

        upper_frame.grid(column=0, row=0, sticky=(N,W,E,S))
        main_lbl.grid(column=0, row=0)
        game_lbl.grid(column=0, row=1)
        game_entry.grid(column=1, row=1)
        goal_lbl.grid(column=0, row=2)
        goal_entry.grid(column=1, row=2)
        adv_btn.grid(column=0, row=3)
        sep.grid(column=1, row=3)

        lower_frame.grid(column=0, row=4, sticky=(N,W,E,S))
        start_lbl.grid(column=0, row=4)
        start_entry.grid(column=1, row=4)
        end_lbl.grid(column=0, row=5)
        end_entry.grid(column=1, row=5)
        weekday_lbl.grid(column=0, row=6)
        weekday_box.grid(column=1, row=6)

        lower_frame.grid_remove()

    def toggle_advanced(self, frame, btn, show):
        """
        Hide/show advanced search options
        """

        if show:
            btn['text'] = "Advanced «"
            frame.grid()
        else:
            btn['text'] = "Advanced »"
            frame.grid_remove()

        
        btn['command'] = lambda: self.toggle_advanced(frame,btn, not show)      

    def create_main_window(self):
        """
        Creates the main window for search
        TODO: Reorganize GUI statments
        """

        root.title("Build Race List")
        c = ttk.Frame(root)

        main_lbl = ttk.Label(c, text='Enter Game Info', font=('Helvetica',16), justify="center")

        game = StringVar()
        game_lbl = ttk.Label(c, text='enter game abbrev:')
        game_entry = ttk.Entry(c, width=23, textvariable=game)

        goal = StringVar()
        goal_lbl = ttk.Label(c, text='goal')
        goal_entry = ttk.Entry(c, width=23, textvariable=goal)

        startdate = StringVar()
        start_lbl = ttk.Label(c, text='enter startdate:')
        start_entry = ttk.Entry(c, width=23, textvariable=startdate)

        enddate = StringVar()
        end_lbl = ttk.Label(c, text='enter enddate:')
        end_entry = ttk.Entry(c, width=23, textvariable=enddate)

        weekday = StringVar()
        weekday_lbl = ttk.Label(c, text='weekday:')
        weekday_box = ttk.Combobox(c, values=('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'), textvariable=weekday)

        buildlist_btn = ttk.Button(c, text="Build Race List", command=lambda: self.show_race_editor(game.get(), goal.get(), self.create_DT(startdate.get()), self.create_DT(enddate.get()), self.get_weekday(weekday.get())))

        c.grid(column=0, row=0, sticky=(N,W,E,S))
        game_lbl.grid(column=0, row=0)
        game_entry.grid(column=1, row=0)
        goal_lbl.grid(column=0, row=1)
        goal_entry.grid(column=1, row=1)
        start_lbl.grid(column=0, row=2)
        start_entry.grid(column=1, row=2)
        end_lbl.grid(column=0, row=3)
        end_entry.grid(column=1, row=3)
        weekday_lbl.grid(column=0, row=4)
        weekday_box.grid(column=1, row=4)
        buildlist_btn.grid(column=1, row=5, sticky=(E,W))

    def show_race_editor(self, *args):
        """
        Build list of races based on args
        Create window+frame to for race editor
        """

        #build arguments for api
        game_name = args[0]
        kw_args = {
            'goal_string': args[1],
            'start_date': args[2] or datetime.datetime(2009,1,1),
            'end_date': args[3] or datetime.datetime.now(),
            'weekdays': args[4]
        }
        print('kw_args = ', kw_args)

        the_races = api.grab(game_name, **kw_args)

        # tables in database for stats
        self.stats.create_tables(game_name)

        # ##########################
        # GUI STUFF

        #create new window + frame
        race_editor = Toplevel(self)
        race_frame = ttk.Frame(race_editor)

        #make labels and gen buttons
        frame_lbl = ttk.Label(race_frame, text='View/Edit Race List', font=('Helvetica',16), justify="center")
        game_lbl = ttk.Label(race_frame, text='Game: '+ game_name, font=('Helvetica', 12))
        goal_lbl = ttk.Label(race_frame, text='Goal: ' + args[1], font=('Helvetica', 12))
        gen_btn = ttk.Button(race_frame, text='Generate Player Records', command=lambda: self.make_records(race_tree, game_name))
        gen_btn2 = ttk.Button(race_frame, text='Generate Race Stats', command=lambda: self.write_records(self.stats.build_race_stats(self.get_race_ids_from_tree(race_tree)), game_name, 'racestat'))

        #make lower frame with edit buttons
        btn_frame = ttk.Frame(race_frame)
        remove_btn = ttk.Button(btn_frame, text='Remove Race', command=lambda: self.remove_race(race_tree, race_tree.focus()))
        add_race_btn = ttk.Button(btn_frame, text='Add Races by ID', command=lambda: self.prompt_for_add_race(race_tree, game_name))
        
        filter_weekly_btn = ttk.Button(btn_frame, text='Filter Weeklys', command=lambda: self.filter_weeklys(race_tree))
        filter_weekly_btn.state(['disabled'])

        check_alts_btn = ttk.Button(btn_frame, text='Check For Missed Weeklys', command=lambda: self.check_alternatives(race_tree, race_tree.item(race_tree.focus())['values'][4], game_name))
        check_alts_btn.state(['disabled'])
        
        #if searching for weekly
        if args[-1]:
            filter_weekly_btn.state(['!disabled'])
            check_alts_btn.state(['!disabled'])

        #make tree view and scroll bar
        race_tree, scroll_bar = self.make_race_tree(race_frame, 25)
        
        #add race and results to tree view
        self.add_races_to_tree(race_tree, the_races, game_name)

        #add widgets to the grid
        race_frame.grid(column=0,row=0,sticky=(N,W,E,S))
        frame_lbl.grid(column=0, row=0)
        game_lbl.grid(column=0, row=1, sticky=(W))
        goal_lbl.grid(column=0, row=2, sticky=(W))
        gen_btn.grid(column=0, row=1, sticky=(E))
        gen_btn2.grid(column=0, row=2, sticky=(E))
        race_tree.grid(column=0, row=3, sticky=(N,W,E,S))
        scroll_bar.grid(column=1, row=3, sticky=(N,S))

        #add lower frame
        btn_frame.grid(column=0, row=4, sticky=(W,E))
        remove_btn.grid(column=1, row=0)
        add_race_btn.grid(column=2, row=0)
        filter_weekly_btn.grid(column=3, row=0)
        check_alts_btn.grid(column=4, row=0)

    def make_race_tree(self, frame, height):
        """
        Creates a treeview widget of races of specified height
        Returns tree and x/y scroll bars
        """

        race_tree = ttk.Treeview(frame, columns=('id', 'date', 'goal', 'numentrants', 'timestamp'), displaycolumns=('id', 'date', 'goal', 'numentrants'), height=height)

        race_tree.heading('id', text="Race ID", command=lambda: self.sort_tree_column_int(race_tree, 'id', False))
        race_tree.heading('date', text='Date Recorded', command=lambda: self.sort_tree_column(race_tree, 'date', False))
        race_tree.heading('goal', text='Goal', command=lambda: self.sort_tree_column(race_tree, 'goal', False))
        race_tree.heading('numentrants', text= "Entrants", command=lambda: self.sort_tree_column_int(race_tree, 'numentrants', False))

        race_tree.column('#0', width=10)
        race_tree.column('id', width=100, anchor=E)
        race_tree.column('date', width=150, anchor=E)
        race_tree.column('goal', width=150, anchor=E)
        race_tree.column('numentrants', width=75, anchor=E)

        scroll_bar = ttk.Scrollbar(frame, orient=VERTICAL, command=race_tree.yview)
        race_tree.configure(yscrollcommand=scroll_bar.set)

        return race_tree, scroll_bar

    def make_player_tree(self, frame):
        """
        Make Treeview for player records
        """

        player_tree = ttk.Treeview(frame, columns=("name", "joins", "avgtime", "first", "second", "third", "winrate", "top3", "quits", "quitrate"), height=25)

        #adjust column headers
        player_tree.heading("name", text="Player Name", command=lambda: self.sort_tree_column(player_tree, "name", False))
        player_tree.heading("joins", text= "Joins", command=lambda: self.sort_tree_column_int(player_tree, "joins", False))
        player_tree.heading("avgtime", text= "Average Time", command=lambda: self.sort_tree_column(player_tree, "avgtime", False))
        player_tree.heading("first", text= "First", command=lambda: self.sort_tree_column_int(player_tree, "first", False))
        player_tree.heading("second", text= "Second", command=lambda: self.sort_tree_column_int(player_tree, "second", False))
        player_tree.heading("third", text= "Third", command=lambda: self.sort_tree_column_int(player_tree, "third", False))
        player_tree.heading("winrate", text= "Win Rate", command=lambda: self.sort_tree_column_flt(player_tree, "winrate", False))
        player_tree.heading("top3", text= "Top3 Rate", command=lambda: self.sort_tree_column_flt(player_tree, "top3", False))
        player_tree.heading("quits", text= "Quits", command=lambda: self.sort_tree_column_int(player_tree, "quits", False))
        player_tree.heading("quitrate", text= "Quit Rate", command=lambda: self.sort_tree_column_flt(player_tree, "quitrate", False))

        #adjust column widths
        player_tree.column("#0", width=10)
        player_tree.column("name", width=100, anchor=E)
        player_tree.column("joins", width=50, anchor=E)
        player_tree.column("avgtime", width=85, anchor=E)
        player_tree.column("first", width=50, anchor=E)
        player_tree.column("second", width=50, anchor=E)
        player_tree.column("third", width=50, anchor=E)
        player_tree.column("winrate", width=100, anchor=E)
        player_tree.column("top3", width=100, anchor=E)
        player_tree.column("quits", width=50, anchor=E)
        player_tree.column("quitrate", width=100, anchor=E)

        scroll_bar = ttk.Scrollbar(frame, orient=VERTICAL, command=player_tree.yview)
        player_tree.configure(yscrollcommand=scroll_bar.set)

        return player_tree, scroll_bar
        
    def add_races_to_tree(self, tree, races, game_name):
        """
        Adds list of races and results to given tree
        Also updates DB tables for stat records
        """

        if not races:
            return

        #add races to tables in database for stats
        self.stats.add_to_tables(races)

        race_gen = (race for race in races)
        while True:
            try:
                race = next(race_gen)
                item_id = tree.insert('', 'end', values=(race['id'], str(datetime.datetime.utcfromtimestamp(int(race['date']))), race['goal'], len(race['results']), race['date']))

                for result in race['results']:
                    tree.insert(item_id, 'end', values=(result['place'], result['player'], self.convert_time(result['time']), result['message']))
            except StopIteration:
                break

    def filter_weeklys(self, tree):
        """
        Filter list of races in tree by num_entrants
        Resulting tree contains one race per week
        """
        
        rows = tree.get_children()
        rows_to_remove = []
        i = 0
        while i < len(rows):
            #print('checking', tree.item(rows[i]), tree.item(rows[j]))
            current_date = tree.item(rows[i])['values'][4]
            j = i+1
            same_days = [rows[i]]
            while j < len(rows):
                if current_date - tree.item(rows[j])['values'][4] < 172800:
                    print('same day found!', tree.item(rows[i]), tree.item(rows[j]))
                    same_days.append(rows[j])
                    j += 1
                else:
                    break
            i = j

            #remove same day races that are less than max_num_entrants
            max_num_entrants = max([tree.item(row)['values'][3] for row in same_days])
            rows_to_remove.extend([row for row in same_days if tree.item(row)['values'][3] < max_num_entrants])

        #remove rows from tree
        print('removing rows = ', rows_to_remove)
        self.remove_many(tree, rows_to_remove)

    def check_weeklys(self, tree):
        """
        Checks given tree for false positives
        """
        rows = tree.get_children()

        #get average entrants
        total_entrants = 0
        for row in rows:
            total_entrants += tree.item(row)['values'][3]

        avg_entrants = total_entrants/len(rows)
        print('avg entrants = ', avg_entrants)
        for row in rows:
            if tree.item(row)['values'][3] < avg_entrants*.4:
                print('low row found!')
                tree.item(row)['tags'] = 'low'
                print('tags = ', tree.item(row)['tags'])

        tree.tag_configure('low', background='green')

        #check gaps
        #for i in range(len(rows)-1):
            #if tree.item(rows[i+1])['values'][4] - tree.item(rows[i])['values'][4] > 864000:
               # pass
                

    def get_race_ids_from_tree(self, tree):
        """
        Return list of race ids from race tree
        """
        rows = tree.get_children()
        race_ids = []
        for row in rows:
            race_ids.append(tree.item(row)['values'][0])
        
        return race_ids

    def make_records(self, race_tree, game_name):
        """
        Generates player records
        Gets target race IDs from list of races in race_tree
        Query results table to build a record for each player
        """
        
        #grab all race ids from tree
        race_ids = self.get_race_ids_from_tree(race_tree)

        #query database with desired ids
        players = self.stats.build_player_records(race_ids)
        
        #make new frame/window for player tree
        t = Toplevel(self)
        c = ttk.Frame(t)
        rec_lbl = ttk.Label(c, text="Player Records for "+game_name, font=('Helvetica',16), justify="center")

        player_tree, scroll_bar = self.make_player_tree(c)

        for player in players:
            player_tree.insert('', 'end', values=(player.get_name(), player.get_joins(), self.convert_time(player.get_average_time()), player.get_ranking(1), player.get_ranking(2), player.get_ranking(3), player.get_win_rate(), player.get_top3_rate(), player.get_quits(), player.get_quit_rate()))

        exp_btn = ttk.Button(c, text="Export to .csv file", command=lambda: self.write_records([player_tree.item(child)['values'] for child in player_tree.get_children()], game_name, 'player'))

        c.grid(column=0, row=0, sticky=(N,W,E,S))
        rec_lbl.grid(column=0, row=0)
        player_tree.grid(column=0, row=1)
        scroll_bar.grid(column=1, row=1, sticky=(N,S,E))
        exp_btn.grid(column=0, row=2, sticky=(W,E))

    def check_alternatives(self, main_tree, race_date, game_name):
        """
        Create new frame and tree view containing alternate weekly races
        """
        the_races = api.grab_nearby(race_date, game_name)

        #create new window and frame
        t = Toplevel(self)
        c = ttk.Frame(t)

        #create alt tree and labels
        alt_lbl = ttk.Label(c, text="List of Possible Missed Weeklys")
        alt_lbl2 = ttk.Label(c, text="(all races in game that have occured 2 weeks from time frame)")
        alt_tree, scroll_bar = self.make_race_tree(c, 15)

        #add races to alt tree
        self.add_races_to_tree(alt_tree, the_races, game_name)

        #create add to main tree button
        add_race_btn = ttk.Button(c, text="Add race to main list", 
               command=lambda: self.add_races_to_tree(main_tree,  
               [the_races[alt_tree.index(alt_tree.focus())]], game_name))

        c.grid(column=0, row=0, sticky=(N,W,E,S))
        alt_lbl.grid(column=0, row=1)
        alt_lbl2.grid(column=0, row=2)
        alt_tree.grid(column=0, row=3, sticky=(N,W,E,S))
        scroll_bar.grid(column=0, row=3, sticky=(N,S,E))
        add_race_btn.grid(column=0, row=4, sticky=(W,E))

    def prompt_for_add_race(self, race_tree, game_name):
        """
        Create and show prompt for adding race
        """
        #create new window
        t = Toplevel(self)
        c = ttk.Frame(t)

        #create widgets
        srl_id = StringVar()
        id_lbl = ttk.Label(c, text='Enter SRL Race ID')
        id_entry = ttk.Entry(c, width=20, textvariable=srl_id)
        add_btn = ttk.Button(c, text="Add Race ID", command=lambda: self.add_races_to_tree(race_tree, api.grab_single(srl_id.get()), game_name))

        #add to grid
        c.grid(column=0,row=0,sticky=(N,W,E,S))
        id_lbl.grid()
        id_entry.grid()
        add_btn.grid()

    def remove_race(self, tree, row):
        """
        Removes race from tree and tables
        """

        self.stats.remove_from_tables(tree.item(row)['values'][0])
        tree.delete(row)

    def remove_many(self, tree, rows):
        """
        Remove many races from tree and tables
        """

        race_ids = []
        for row in rows:
            race_ids.append(tree.item(row)['values'][0])
            tree.delete(row)

        self.stats.remove_many_from_tables(race_ids)

    def write_records(self, rows, game_name, rec_type):
        """
        Write stat records to a csv file from given rows
        """
        
        path_of_records = os.path.dirname(os.path.abspath(__file__))
        file_name = path_of_records+'\\'+game_name+rec_type+'record.csv'

        with open(file_name, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter='\t')
            for row in rows:
                csv_writer.writerow(row)

        #open file with user's default program
        os.startfile(file_name)

    def create_DT(self, dateline):
        """
        Convert dateline string mm/dd/yyyy to datetime object
        """

        if not dateline:
            return ''

        datebreak = dateline.split('/')	

        if len(datebreak) != 3:
            return ''

        month = int(datebreak[0])
        day = int(datebreak[1])
        yr = int(datebreak[2])

        return datetime.datetime(yr, month, day)

    def get_weekday(self, weekday):
        """
        Return numerical version of weekday + day after
        For weekly searches
        """

        return {
               '': None,
            'Mon': (0,1),
            'Tue': (1,2),
            'Wed': (2,3),
            'Thu': (3,4),
            'Fri': (4,5),
            'Sat': (5,6),
            'Sun': (6,0)
        }[weekday]

    def convert_time(self, racetime):
        """
        Converts time in seconds to hh:mm:ss for display
        """

        if racetime == 'DQ' or racetime == 'Quit' or racetime == 'DNF':
            return racetime
        elif racetime > 3599:
            hh = math.floor(racetime/3600)
            mm = math.floor((racetime-(3600*hh))/60)
            ss = racetime-((3600*hh)+(60*mm))
        elif racetime > 59:
            hh = 0
            mm = math.floor(racetime/60)
            ss = (racetime-(60*mm))
        else:
            hh = 0
            mm = 0
            ss = racetime

        formattedtime = "%02d:%02d:%02d" % (hh, mm, ss)
        return formattedtime

    def sort_tree_column_int(self, tree, col, reverse):
        """
        Sort tree view for columns containing integers
        """

        #first sort items
        items = [(tree.set(k, col), k) for k in tree.get_children('')]
        items.sort(key=lambda t: int(t[0]), reverse=reverse)
        
        #rearrange items in tree into sorted positions
        for i, (val, k) in enumerate(items):
            tree.move(k, '', i)

        #flip reverse for next click
        tree.heading(col, command=lambda: self.sort_tree_column_int(tree, col, not reverse))

    def sort_tree_column_flt(self, tree, col, reverse):
        """
        Sort tree view for columns containing integers
        """

        #first sort items
        items = [(tree.set(k, col), k) for k in tree.get_children('')]
        items.sort(key=lambda t: float(t[0]), reverse=reverse)
        
        #rearrange items in tree into sorted positions
        for i, (val, k) in enumerate(items):
            tree.move(k, '', i)

        #flip reverse for next click
        tree.heading(col, command=lambda: self.sort_tree_column_flt(tree, col, not reverse))

    def sort_tree_column(self, tree, col, reverse):
        """
        Sort tree view for columns containing non-numbers
        """

        #get all items
        items = [(tree.set(k, col), k) for k in tree.get_children('')]
        items.sort(reverse=reverse)
        
        #rearrange items in sorted positions
        for i, (val, k) in enumerate(items):
            tree.move(k, '', i)

        #flip reverse for next click
        tree.heading(col, command=lambda: self.sort_tree_column(tree, col, not reverse))

#create main window and content frame
root = Tk()
app = SRLStatsApp(master=root)
app.mainloop()
