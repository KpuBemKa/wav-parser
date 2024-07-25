# wav-parser
Receives wav files with speech from esp-recorder, and parses them into text

# Prepare the python environment:
```.sh
python3 -m venv venv
```
```.sh
source venv/bin/activate
```
```.sh
pip install -r .\requirements.txt
```
```.sh
pip install --upgrade transformers optimum accelerate
```

## Install `flash-attn` optimization option:
Note: not available on all GPUs. Check if available on yours

```.sh
pip install packaging wheel
```

Ensure ninja is installed for faster compiling:
Check Ninja Version:
```.sh
ninja --version
``` 
If not installed:
```.sh
pip install ninja
```

```.sh
pip install flash-attn --no-build-isolation
````

Then you can check after success installation with:
```.py
from transformers.utils import is_flash_attn_2_available
print(is_flash_attn_2_available())
````
Should return `True` if installed, `False` otherwise