# mantra
Its all about the reps


# initial setup

```console
# my system-wide installs (or install in venv if you like)
zsh                                  # goto zsh (not the default yet)
sudo apt-get install python3-venv    # even though 16.04 comes with python3
sudo apt-get install pandoc          # used by pypandoc

cd ~/dev
git clone https://github.com/hertogp/mantra

cd mantra                            # make a venv in dev-dir itself
python3 -m venv venv
. venv/bin/activate                  # aliased to v.on
pip install --upgrade pip            # version 9.0.2
pip install -r requirements.txt      # now installs newer ruamel.yaml
ln -s ~/dev/mantra/mantra.py ~/bin/mantra

cd <root-dir>                        # TopDir with docs underneath
mkdir mantra                         # - mantras top output dir
ln -s ~/dev/mantra/static <root-dir>/mantra/static
mantra
```

