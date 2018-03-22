from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'width', '960')
Config.set('graphics', 'height', '540')
Config.set('graphics', 'fullscreen','auto')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
import time
import glob
import os
from functools import partial
#import cProfile
#from random import shuffle

class ListButton(Button):
    pass
    
class ConfigPopup(Popup):
    pass
            
class SelectionScreen(Screen):

    # Default localization strings
    current_lang = 'lang1' 
    
    # List to store selected choices
    selection_list = list()

    # Default video
    current_video = 'attractor'
    
    # Holds the name of the recently-pressed button to fight button mashing
    blocked = ''
    
    def localize(self):
        # Function to localize the text
        
        #self.manager.debug_list.append(('localize:',time.time()))

        for child in self.ids['button_bar'].children:
            index = self.manager.button_ids.index(child.id)
            if self.current_lang == 'lang1': # Switch to secondary language
                child.text = self.manager.button_text_lang2[index]
                child.background_normal = self.manager.button_background_normal_lang2[index]
                child.background_down = self.manager.button_background_down_lang2[index]
            elif self.current_lang == 'lang2': # Switch to primary language
                child.text = self.manager.button_text_lang1[index]
                child.background_normal = self.manager.button_background_normal_lang1[index]
                child.background_down = self.manager.button_background_down_lang1[index]

        if self.current_lang == 'lang1': # Switch to secondary langauge
            self.current_lang = 'lang2'
            self.lang_switch.text = self.manager.lang1_switch_text
        elif self.current_lang == 'lang2': # Switch to primary language
            self.current_lang = 'lang1'
            self.lang_switch.text = self.manager.lang2_switch_text

        # Reload the video in the new language
        self.choose_video(self.current_video, None, noblock=True)
        
    def unblock(self, choice, dt):
        # Function to lift the block on a given button
        
        #self.manager.debug_list.append(('unblock:',time.time()))
        
        if self.blocked == choice:
            self.blocked = ''
            
    def choose_video(self, choice, button, loop=False, noblock=False):
        # Function called when a button is pressed
        # button is a dummy entry; ignore it

        #self.manager.debug_list.append(('chose_video:',time.time()))
        if self.blocked != choice or noblock: # Fight button mashing
        
            #self.manager.debug_list.append(('chose_video: not blocked',time.time()))
        
            if not noblock:
                self.blocked = choice
                Clock.schedule_once(partial(self.unblock,choice), 2)
        
            # Log the choice for analytics
            self.selection_list.append((choice, time.time()))
       
            # Build the proper language suffix
            lang = '_' + self.current_lang
            
            # Switch the video source

            if choice == 'attractor':
                #self.manager.debug_list.append(('chose_video: attractor',time.time()))
                if self.current_lang == 'lang1':
                    source = self.manager.attractor_lang1
                else:
                    source = self.manager.attractor_lang2
            else:
                #self.manager.debug_list.append(('chose_video: ' + choice,time.time()))
                for i in range(len(self.manager.button_ids)):
                    if choice == self.manager.button_ids[i]:
                        base_file = self.manager.button_video_file[i]
                        
                        # This reverses the string, splits the first . (the extension)
                        split = base_file[::-1].split('.',1)

                        # This unreverses and rejoins the string with the language prefix  
                        source = split[1][::-1] + lang + '.' + split[0][::-1]
                        
            # Normalize the slashes in the path 
            source = os.path.normpath(source)
                        
            # Reset the player
            self.player.unload()
            self.player.source = source
            self.player.state = 'play'
            if loop:
                self.player.options['eos'] = 'loop'
            else:
                self.player.options['eos'] = 'stop'

            self.current_video = choice
        self.manager.ticks_idle = 0
        
    def __init__(self, **kwargs):        
        super(Screen,self).__init__(**kwargs)
    
class ScreenManagement(ScreenManager):

    # Default parameter values

    ticks_idle = 0 # 1 tick per second
    #debug_list = list() # For debugging
    
    button_ids = list()
    button_video_file = list()
    button_text_lang1 = list()
    button_text_lang2 = list()
    button_background_down_lang1 = list()
    button_background_normal_lang1 = list()
    button_background_down_lang2 = list()
    button_background_normal_lang2 = list()
    path = ''

    lang1_switch_text = ''
    lang2_switch_text = ''
    attractor_lang1 = ''
    attractor_lang2 = ''
    button_background_normal = 'atlas://data/images/defaulttheme/button'
    button_background_down = 'atlas://data/images/defaulttheme/button_pressed'
    lang_switch_background_normal = 'atlas://data/images/defaulttheme/button'
    lang_switch_background_down = 'atlas://data/images/defaulttheme/button_pressed'
    
    # These control whether or not the button to switch languages appears
    lang_switch_opacity = 1
    lang_switch_size_hint = (1, 0.1)
    lang_switch_disabled = False
    
    font_button = 'Roboto-Bold.ttf'
    font_lang_switch = 'Roboto-Regular.ttf'

    def check_for_idle(self, dt):
        # Function to watch for idle and reset the screenmanager
    
        if self.get_screen('selection').player.state == 'stop':
            #self.debug_list.append(('check_for_idle: player stopped, checking idle',time.time()))
            if self.ticks_idle < 60:
                self.ticks_idle += 1
            else:
                self.get_screen('selection').choose_video('attractor', None, True)
                if self.get_screen('selection').current_lang == 'lang2':
                    self.get_screen('selection').localize()
                self.ticks_idle = 0
                
    def write_analytics(self, dt):
        # Function to periodically write the latest analytics data to file
        
        #self.debug_list.append(('write_analytics:',time.time()))
        
        with open('analytics.csv', 'a') as f:
            for entry in self.get_screen('selection').selection_list:
                f.write(entry[0]+', '+str(entry[1])+'\n')
                
        # with open('debug.csv', 'a') as f:
            # for entry in self.debug_list:
                # f.write(entry[0]+', '+str(entry[1])+'\n')
            
        self.get_screen('selection').selection_list = list()
        #self.debug_list = list()

    def populate_button_bar(self,dt):
        # Function to populate the left bar with buttons defined by the 'entries' directory
        
        #self.debug_list.append(('populate_button_bar:',time.time()))
        
        # Find button definition files
        files = glob.glob(self.path+'entries/*.conf')
        
        # For each file, add a button to the interface
        for file in files:
            with open(file, 'r', encoding='utf8') as f:

                text_lang1 = ''
                text_lang2 = ''
                video_file = ''
                button_background_down_lang1 = self.button_background_down
                button_background_normal_lang1 = self.button_background_normal
                button_background_down_lang2 = self.button_background_down
                button_background_normal_lang2 = self.button_background_normal

                for line in f: # Parse the definition file for keywords
                    if line[0:6].lower() == 'lang1:':
                        text_lang1 = line[6:].strip().replace('\\n', '\n')
                    if line[0:6].lower() == 'lang2:':
                        text_lang2 = line[6:].strip().replace('\\n', '\n')
                    elif line[0:5].lower() == 'file:':
                        video_file = self.path+line[5:].strip()
                    elif line[0:31].lower() == 'button_background_normal_lang1:': # Per-button override
                        button_background_normal_lang1 = line[31:].strip()
                    elif line[0:29].lower() == 'button_background_down_lang1:': # Per-button override
                        button_background_down_lang1 = line[29:].strip()
                    elif line[0:31].lower() == 'button_background_normal_lang2:': # Per-button override
                        button_background_normal_lang2 = line[31:].strip()
                    elif line[0:29].lower() == 'button_background_down_lang2:': # Per-button override
                        button_background_down_lang2 = line[29:].strip() 

                # id is everything but the file extension; must be unique
                id = video_file[::-1].split('.',1)[1][::-1]
                
                # Create the button
                button = ListButton(background_down = button_background_down_lang1,
                    background_normal = button_background_normal_lang1,
                    font_name = self.font_button,
                    font_size = 25,
                    halign = 'center',
                    id = id,
                    markup = True,
                    text = text_lang1,
                    text_size = (self.width*0.95, self.height*0.95),
                    valign = 'center')
                    
                button.bind(on_release=partial(self.get_screen('selection').choose_video,id))
                self.get_screen('selection').button_bar.add_widget(button)

                # Store things for later
                self.button_text_lang1.append(text_lang1)
                self.button_text_lang2.append(text_lang2)
                self.button_background_down_lang1.append(button_background_down_lang1)
                self.button_background_normal_lang1.append(button_background_normal_lang1)
                self.button_background_down_lang2.append(button_background_down_lang2)
                self.button_background_normal_lang2.append(button_background_normal_lang2)
                self.button_ids.append(id)
                self.button_video_file.append(video_file)
                
    def get_config(self, file='config.conf'):
        # Function to read a configuration file and get things going
        
        #self.debug_list.append(('get_config:',time.time()))
        
        self.path = os.path.join(os.path.dirname(file),'')
        
        if os.path.isfile(file):
            with open(file, 'r', encoding='utf8') as f:
                for line in f:
                    if line[0:18].lower() == 'switch_text_lang1:':
                        self.lang1_switch_text = line[18:].strip().replace('\\n', '\n')
                    elif line[0:18].lower() == 'switch_text_lang2:':
                        self.lang2_switch_text = line[18:].strip().replace('\\n', '\n')
                    elif line[0:16].lower() == 'attractor_lang1:':
                        self.attractor_lang1 = self.path + line[16:].strip()
                    elif line[0:16].lower() == 'attractor_lang2:':
                        self.attractor_lang2 = self.path + line[16:].strip()
                    elif line[0:12].lower() == 'font_button:':
                        self.font_button = line[12:].strip()
                    elif line[0:17].lower() == 'font_lang_switch:':
                        self.font_lang_switch = line[17:].strip()
                    elif line[0:25].lower() == 'button_background_normal:':
                        self.button_background_normal = line[25:].strip()
                    elif line[0:23].lower() == 'button_background_down:':
                        self.button_background_down = line[23:].strip()
                    elif line[0:30].lower() == 'lang_switch_background_normal:':
                        self.lang_switch_background_normal = line[30:].strip()                        
                    elif line[0:28].lower() == 'lang_switch_background_down:':
                        self.lang_switch_background_down = line[28:].strip() 
                    elif line[0:20].lower() == 'disable_lang_switch:':
                        if line[20:].strip().lower() == 'true':
                            self.lang_switch_opacity = 0
                            self.lang_switch_size_hint = (1, None)
                            self.lang_switch_disabled = True

            # Configuration file read, let's start up the rest of the app
            self.add_widget(SelectionScreen())
            Clock.schedule_once(self.populate_button_bar)
            Clock.schedule_interval(self.check_for_idle, 1.) # Once per second
            Clock.schedule_interval(self.write_analytics, 3600.) # Once per hour
            #Clock.schedule_interval(self.test_cycler, 5.)
        else:
            ConfigPopup().open()
            
    # def test_cycler(self, dt):
        # vids = list(['attractor', 'media/ural', 'media/arctic', 'media/heat', 'media/antarctica', 'media/glacier'])
        # shuffle(vids)
        # self.get_screen('selection').choose_video(vids[0],None)      
                    
    def __init__(self):
        #self.debug_list.append(('__init__',time.time()))
        super(ScreenManagement, self).__init__()   
        
        
class MainApp(App):

    def build(self):
        self.manager = ScreenManagement()
        self.manager.get_config()
        #self.profile = cProfile.Profile()
        #self.profile.enable()
        return(self.manager)
        
    def on_stop(self):
        self.manager.write_analytics('')
        #self.profile.disable()
        #self.profile.dump_stats('myapp.profile')
        #pdb.set_trace()

MainApp().run()














