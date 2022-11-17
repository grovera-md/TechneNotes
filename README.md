<p align="center">
    <img alt="logo" src="./data/sample_media/technenotes_icon.png">
</p>

#TechneNotes

### Installation instructions
Note: Since TechneNotes is a newly developed project, there isn't a `.deb` package yet, so the software is currently not available through the software manager.

1. Before installing TechneNotes, you MUST install its dependencies  
Install the `meson`, `python3-peewee`, `python3-markdown`, and `python3-lxml` packages through the software manager
2. Download the Github compressed project folder on your computer (e.g. `/home/[user]/TechneNotes`).  
3. Extract the compressed folder. Inside the `/home/[user]/TechneNotes` folder you should now have a series of files and folders (e.g. `meson.build`, `src`)

Now install the software using one of the following methods. It is recommended to use the provided install script (method 1).

#### Method 1: Install with the provided install script (*recommended*)
4. Open a terminal and cd into the main folder of the project
5. Give the shell permission to execute the install script: `chmod 755 install.sh`
6. Run `./install.sh` (do NOT run the command with `sudo` - The script will automatically ask for superuser privileges when needed)
7. Launch the software with the newly created menu entry or `cd` into the `src` folder and launch `python3 technenotes.py`
Note: for TechneNotes to appear in the start menu, you may need to log out and log back in (this will refresh the start menu) or restart the pc

#### Method 2: Manual Meson install (*to debug any problem with the provided install script*)
4. Open a terminal and cd into the main folder of the project
5. Run `meson setup builddir` to initialize the build
6. Cd into the build folder: `cd builddir`
7. Build the code by running `ninja` (if Meson version <= 0.55.0) or `meson compile` (if Meson version > 0.55.0)
8. Install files by running `ninja install` (if Meson version <= 0.55.0) or `meson install` (if Meson version > 0.55.0)
9. Launch the software with the newly created menu entry or `cd` into the `src` folder and launch `python3 technenotes.py`
Note: for TechneNotes to appear in the start menu, you may need to log out and log back in (this will refresh the start menu) or restart the pc

#### Method 3: Complete manual installation (*only if previous methods fail*)
- GSettings files  
  Copy the `data/ovh.technenotes.myapp.gschema.xml` file into the `/usr/local/share/glib-2.0/schemas` directory  
  Then, run the  command `glib-compile-schemas /usr/local/share/glib-2.0/schemas/`
- GtkSource syntax highlighting files  
  Copy the `data/markdown-extra-tech.lang` file into the `/usr/local/share/gtksourceview-3.0/language-specs/` directory
  Copy the `data/codezone-tech.xml` file into the `/usr/local/share/gtksourceview-3.0/styles/` directory
- Add the `Lato-Regular` font to the system fonts  
  Copy the `data/Lato-Regular.ttf` and `data/SIL Open Font License.txt` to the `/usr/local/share/fonts/Lato-Regular` directory
- Launch the software 
  Use the newly created menu entry or `cd` into the `src` folder and launch `python3 technenotes.py`
  For TechneNotes to appear in the start menu, you may need to log out and log back in (this will refresh the start menu) or restart the pc
  
Note: instead of the `usr/local/...` path you can also use `/home/[user]/.local/...`. The difference is that `usr/local` is used for a system-wide installation while `/home/[user]/.local/...` only works for the current user. 

### Uninstall instructions

Uninstall the software using one of the following methods. It is recommended to use the provided uninstall script (method 1).

#### Method 1: Uninstall with the provided uninstall script (*recommended*)
1. Open a terminal and cd into the main folder of the project
2. Give the shell permission to execute the uninstall script: `chmod 755 uninstall.sh`
3. Run `./uninstall.sh` (do NOT run the command with `sudo` - The script will automatically ask for superuser privileges when needed)

#### Method 2: Manual Meson uninstall (*to debug any problem with the provided uninstall script*)
1. Open a terminal and cd into the main folder of the project
2. Cd into the build folder: `cd builddir`
3. Install files by running `ninja uninstall` (if Meson version <= 0.55.0) or `meson uninstall` (if Meson version > 0.55.0)
4. Reset the software GSettings by running `gsettings reset-recursively ovh.technenotes.myapp` (or manually delete the GSettings entry `ovh.technenotes.myapp` using the `dconf-editor` GUI application)

#### Method 3: Complete manual uninstall (*only if previous methods fail*)
- GSettings files  
  Delete the `ovh.technenotes.myapp.gschema.xml` file from the `/usr/local/share/glib-2.0/schemas` directory  
  Then, run the  command `glib-compile-schemas /usr/local/share/glib-2.0/schemas/`
- GtkSource syntax highlighting files  
  Delete the `markdown-extra-tech.lang` file from the `/usr/local/share/gtksourceview-3.0/language-specs/` directory
  Delete the `codezone-tech.xml` file from the `/usr/local/share/gtksourceview-3.0/styles/` directory
- Remove the `Lato-Regular` font from the system fonts  
  Delete the `Lato-Regular.ttf` and `SIL Open Font License.txt` from the `/usr/local/share/fonts/Lato-Regular` directory
  
Note (about method 3):  
In the above steps, use the `usr/local/...` path if:
- you installed the software with either method 1 or 2
- you installed the software with method 3, and you used the `usr/local` path to perform a system-wide installation  

In the above steps, use the `/home/[user]/.local/...` path if:
- you installed the software with method 3, and you used the `/home/[user]/.local/...` path to make changes only for the current user.  

### Known minor issues

#### Javascript syntax highlighting in markdown editor
*Problem:*  
In some newer distributions, the javascript syntax is not properly highlighted in the markdown editor, due to the system lang definition in the `javascript.lang` file.

*Solution:*  
Copy the `data/javascript.lang` file into the `/usr/local/share/gtksourceview-3.0/language-specs/` folder.  
This will simply override the syntax definition. You can easily revert back to the default by deleting the file.
