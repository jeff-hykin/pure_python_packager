Under construction

# What is this?

A tool for publishing existing python packages in a way that bundles their dependencies.

# How do I use this?

To add a dependency:

```sh
# most basic
pure_python_packager --add git@github.com:jeff-hykin/blissful_basics.git --as blissful_basics

# more options
pure_python_packager \
    --add git@github.com:jeff-hykin/blissful_basics.git \
    --as blissful_basics \
    --at 0.2.27 \
    --module_path main/blissful_basics
```

To use that dependency:

```py
from .__dependencies__ import blissful_basics
```

# How do I install this?

Make sure you have git installed

`pip install pure_python_packager`

Make sure you have [git subrepo](https://github.com/ingydotnet/git-subrepo) installed
```sh
mkdir -p "$HOME/repos/"
cd "$HOME/repos/"
git clone https://github.com/ingydotnet/git-subrepo
echo 'source "$HOME/git-subrepo/.rc"' >> ~/.bashrc
source "$HOME/git-subrepo/.rc"
```
