from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'width', '960')
Config.set('graphics', 'height', '540')
#Config.set('graphics', 'fullscreen','auto')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
import time
import glob
import os
from functools import partial
            
class SelectionScreen(Screen):

    # Default localization strings
    current_lang = 'lang1' 
    
    # List to store selected choices
    selection_list = list()

    # Default video
    current_video = 'attractor'
    
    def localize(self):
        # Function to localize the text

        for child in self.ids['button_bar'].children:
            index = self.manager.button_ids.index(child.id)
            if self.current_lang == 'lang1': # Switch to secondary language
                child.text = self.manager.button_text_lang2[index]
            elif self.current_lang == 'lang2': # Switch to primary language
                child.text = self.manager.button_text_lang1[index]

        if self.current_lang == 'lang1': # Switch to secondary langauge
            self.current_lang = 'lang2'
            self.lang_switch.text = self.manager.lang1_switch_text
        elif self.current_lang == 'lang2': # Switch to primary language
            self.current_lang = 'lang1'
            self.lang_switch.text = self.manager.lang2_switch_text

        # Reload the video in the new language
        self.choose_video(self.current_video, None)
            
    def choose_video(self, choice, button, loop=False):
        # Function called when a button is pressed
        # button is a dummy entry; ignore it

        # Log the choice for analytics
        self.selection_list.append((choice, time.time()))
   
        # Build the proper language suffix
        lang = '_' + self.current_lang
        
        # Switch the video source

        if choice == 'attractor':
            if self.current_lang == 'lang1':
                source = self.manager.attractor_lang1
            else:
                source = self.manager.attractor_lang2
        else:
            for i in range(len(self.manager.button_ids)):
                if choice == self.manager.button_ids[i]:
                    base_file = self.manager.button_video_file[i]
                    split = base_file.split('.')
                    source = split[0] + lang + '.' + split[1]
  
        # Reset the player
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
    
    button_ids = list()
    button_video_file = list()
    button_text_lang1 = list()
    button_text_lang2 = list()

    lang1_switch_text = ''
    lang2_switch_text = ''
    attractor_lang1 = ''
    attractor_lang2 = ''
    button_background_normal = 'atlas://data/images/defaulttheme/button'
    button_background_down = 'atlas://data/images/defaulttheme/button_pressed'
    lang_switch_background_normal = 'atlas://data/images/defaulttheme/button'
    lang_switch_background_down = 'atlas://data/images/defaulttheme/button_pressed'
    
    font_button = 'Roboto-Bold.ttf'
    font_lang_switch = 'Roboto-Regular.ttf'

    def check_for_idle(self, dt):
        # Function to watch for idle and reset the screenmanager
    
        if self.get_screen('selection').player.state == 'stop':
            if self.ticks_idle < 60:
                self.ticks_idle += 1
            else:
                self.get_screen('selection').choose_video('attractor', None, True)
                if self.get_screen('selection').current_lang == 'lang2':
                    self.get_screen('selection').localize()
                self.ticks_idle = 0
                
    def write_analytics(self, dt):
        # Function to periodically write the latest analytics data to file
        
        with open('analyics.csv', 'a') as f:
            for entry in self.get_screen('selection').selection_list:
                f.write(entry[0]+', '+str(entry[1])+'\n')
            
        self.get_screen('selection').selection_list = list()

    def populate_button_bar(self,dt):
        # Function to populate the left bar with buttons defined by the 'entries' directory

        # Find button definition files
        files = glob.glob('entries/*.conf')
        
        # For each file, add a button to the interface
        for file in files:
            with open(file, 'r', encoding='utf8') as f:

                text_lang1 = ''
                text_lang2 = ''
                video_file = ''

                for line in f: # Parse the definition file for keywords
                    if line[0:6].lower() == 'lang1:':
                        text_lang1 = line[6:].strip().replace('\\n', '\n')
                    if line[0:6].lower() == 'lang2:':
                        text_lang2 = line[6:].strip().replace('\\n', '\n')
                    elif line[0:5].lower() == 'file:':
                        video_file = line[5:].strip()

                # id is the first substring delimited by '.'; must be unique
                id = video_file.split('.')[0]
                
                # Create the button
                button = Button(background_down = self.button_background_down,
                    background_normal = self.button_background_normal,
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
                self.button_ids.append(id)
                self.button_video_file.append(video_file)

    def get_config(self):
        if os.path.isfile('config.conf'):
            with open('config.conf', 'r', encoding='utf8') as f:
                for line in f:
                    if line[0:18].lower() == 'switch_text_lang1:':
                        self.lang1_switch_text = line[18:].strip().replace('\\n', '\n')
                    elif line[0:18].lower() == 'switch_text_lang2:':
                        self.lang2_switch_text = line[18:].strip().replace('\\n', '\n')
                    elif line[0:16].lower() == 'attractor_lang1:':
                        self.attractor_lang1 = line[16:].strip()
                    elif line[0:16].lower() == 'attractor_lang2:':
                        self.attractor_lang2 = line[16:].strip()
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
                        
    def __init__(self):
        super(ScreenManagement, self).__init__()
        self.get_config() # Must be first after super.__init__
        Clock.schedule_once(self.populate_button_bar)
        Clock.schedule_interval(self.check_for_idle, 1.) # Once per second
        Clock.schedule_interval(self.write_analytics, 3600.) # Once per hour
        
class MainApp(App):
    pass

MainApp().run()














