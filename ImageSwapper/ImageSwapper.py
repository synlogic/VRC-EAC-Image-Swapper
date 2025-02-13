from random import choice
from os import path, listdir, getcwd, pardir
from sys import exit, stdout
from glob import glob
from requests import get as rget
from configparser import ConfigParser
from traceback import print_exc, format_exc
from PIL import Image
from packaging import version

def print(value, force=False):
    config = ConfigParser()
    config.read('config.ini')
    if config.get('OPTIONS', 'output_to_cmd').lower() == 'true' or force:
        stdout.write(f'{value}\n')

def CheckForUpdates():
    current_version = "3.0.1"
    print(f"EAC Image Swapper version: {current_version}", True)
    print("Checking for updates | You can disable this in config.ini", True)
    
    try:
        response = rget("https://github.com/synlogic/EAC-Image-Swapper/releases/latest")
        latest = response.url.split('/')[-1].replace('v', '')
        if version.parse(current_version) < version.parse(latest):
            print("\nUpdate Available! Download from \nhttps://github.com/synlogic/EAC-Image-Swapper/releases/latest (Copy Paste into Browser)\n", True)
            input("Press enter key to continue..")
    except Exception:
        print_exc()
        print('Checking for updates failed...', True)
        return

def Resize(path):
    image = Image.open(path)
    
    ratio = min(800 / image.width, 450 / image.height)

    y = int(450)
    x = int(image.width  * ratio)

    image = image.resize((x, y))
    background = Image.new('RGBA', (800, 450), (0,0,0,0))
    offset = ((800 - x) // 2, (450 - y) // 2)
    background.paste(image, offset)
    new_image = background.convert('RGB')

    return new_image

def GenerateConfig():
    sections = ('PATH', 'OPTIONS')
    options = [['PATH', 'photos', ''], ['PATH', 'exclusions', ''],['PATH', 'EasyAntiCheat', './EasyAntiCheat'], ['OPTIONS', 'pause_on_complete', 'false'], ['OPTIONS', 'check_for_updates', 'true'], ['OPTIONS', 'output_to_cmd', 'false']]
    config = ConfigParser()

    config_file_exists = run_bat_exists = True


    #Generate new config
    if (not path.exists('config.ini')):
        config_file_exists = False
        look_for = 'EasyAntiCheat'
        found = False
        actual_path = ""
        root_dir = path.join(getcwd(), pardir)
        for f in listdir(root_dir):
            if f == look_for:
                found = True
                actual_path = path.join(root_dir, f)
                break
        if not found:
            for f in listdir(path.join(root_dir, pardir)):
                if f == look_for:
                    found = True
                    actual_path = path.join(root_dir, pardir, f)
                    break
            if not found:
                print("Configuration was unable to find the EAC location, you will need to manually update this in the config.ini.", True)
        else:
            options[2] = ['PATH', 'EasyAntiCheat', actual_path]

        for section in sections:
            config.add_section(section)
        for option in options:
            config.set(option[0], option[1], option[2])
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print('Add ImageSwapper\\run.bat %COMMAND% to your launch options in Steam then add your actual launch options AFTER', True)
        print("Open config.ini and input your photo path and EAC path (if needed)\n", True)
        
    if not path.exists('run.bat'):
        print("run.bat is missing, this will be generated automatically.", True)
        run_bat_exists = False
        commands = f"@echo off\nset root=./ImageSwapper/\ncd %root%\nstart ImageSwapper.exe\n%*"

        with open('run.bat', 'w') as bfile:
            bfile.write(commands)

    if not run_bat_exists or not config_file_exists:
        #print(f"Config file exists={config_file_exists}, Run.bat exists={run_bat_exists}", True)
        input("\nPress enter key to exit...")
        exit()   

    # Generate missing options
    elif path.exists('config.ini'):
        config.read('config.ini')
        for option in options:
            if config.has_option(option[0], option[1]):
                config.set(option[0], option[1], config.get(option[0], option[1]))
            else:
                if not config.has_section(option[0]):
                    config.add_section(option[0])
                config.set(option[0], option[1], option[2])
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    if config.get('PATH', 'photos') == "":
        input("Open config.ini and input your VRChat photo path and VRChat EAC path | Press enter key to exit.")
        exit()
    return config

def getLastUsedPhoto():
    photo_path = None
    if path.exists('last_used.txt'):
        with open('last_used.txt') as f:
            photo_path = f.read().strip()
    return photo_path

def saveLastUsedPhoto(photo_path):
    print("Saving last used photo")
    with open('last_used.txt', 'w') as f:
        f.write(photo_path)
    
def GetPhotosInDirectory(dir):
    print(f'Finding files in {dir}')
    last_used = getLastUsedPhoto()
    photos = []
    if not path.isdir(dir) and ((dir.lower().endswith('.png') or dir.lower().endswith('.jpg')) and not dir.lower().endswith('_vr.jpg')):
        photos.append(dir)
        try:
            photos.remove(last_used)
        except ValueError:
            pass
        print(photos)
        return photos
    for file in listdir(dir):
        if (file.lower().endswith('.png') or file.lower().endswith('.jpg')) and not file.lower().endswith('_vr.jpg'):
            if file == last_used:
                continue
            path_ = dir + '\\' + file
            print(f'     - {file}')
            photos.append(path_)
    return photos

def run():
    config = GenerateConfig()
    if config.get('OPTIONS', 'check_for_updates').lower() == "true": CheckForUpdates()
    exclusions = config.get('PATH', 'exclusions').split('+')
    paths = config.get('PATH', 'photos').split('+')
    photos = []
    for path_ in paths:
        glob_pattern = path.join(path_, '*')
        photos = photos + GetPhotosInDirectory(path_)
        files = sorted(glob(glob_pattern), key=path.getctime)
        for file in files:
            if path.isdir(file) and not file in exclusions:
                photos = photos + GetPhotosInDirectory(file)
    try:
        if len(photos) <= 1:
            print("Only one photo is available to pick from.  Exiting early to save time.", True)
            if config.get('OPTIONS', 'pause_on_complete').lower() == 'true':
                input("Pause on Complete enabled in config.ini, Press enter key to exit")
            
        new_photo = choice(photos)
    except IndexError:
        print('No photos to be found! Empty photos directory maybe?', True)
        input("Press enter key to exit.")
        exit()
    except:
        print(format_exc(), True)

    saveLastUsedPhoto(path.basename(new_photo))
    scaled = Resize(new_photo)
    eac_path = config.get('PATH', 'EasyAntiCheat')
    scaled.save(f'{ eac_path }\\SplashScreen.png')
    if config.get('OPTIONS', 'pause_on_complete').lower() == 'true':
        print("Image successfully scaled and replaced.", True)
        input("Pause on Complete enabled in config.ini, Press enter key to exit")

if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        print(format_exc(), True)
        input("Something went wrong, Press enter key to exit..")
        exit()