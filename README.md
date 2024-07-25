# wav-parser
Receives wav files with speech from esp-recorder, and parses them into text

# Prepare the python environment:
```.sh
python3 -m venv venv
source venv/bin/activate
pip install -r .\requirements.txt
pip install --upgrade transformers optimum accelerate
```

## Install `flash-attn` optimization option:
Note: not available on all GPUs. Check if available on yours


```.sh
pip install packaging wheel
pip install ninja
pip install flash-attn --no-build-isolation
```

Then you can check after success installation with:
```.py
from transformers.utils import is_flash_attn_2_available
print(is_flash_attn_2_available())
````
Should return `True` if installed, `False` otherwise
