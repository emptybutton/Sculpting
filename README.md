## Sculpting
Library for sculpting objects from others

### Installing
```pip install sculpting```

### Examples
Create an object based on another
```python
from dataclasses import dataclass

from pyhandling import by, then
from sculpting import Sculpture


@dataclass
class User:
    id: int
    username: str
    password: str


original = User(0, "William", "1234")

sculture = Sculpture(
    original,
    name="username",
    password_hash=(getattr |by| "password") |then>> hash
)
```

which is mapped with the original
```python
sculture.name
sculture.password_hash
```
```
William
1670106271132722890
```

even with its modification
```python
sculture.name = "Not William"
original.username
```
```
Not William
```

which can be custom
```python
from sculpting import AttributeMap, changing_attribute_map_for
from sculpting.tools import setting_of_attr


transforming_sculpture = Sculpture(
    original,
    id_of_others=AttributeMap(
        getattr |by| "id_of_others",
        setting_of_attr("id_of_others", value_transformer=tuple)
    ),
    # Shortcut for recording above
    synonym_for_id_of_others=changing_attribute_map_for("id_of_others", tuple)
)

transforming_sculpture.synonym_for_id_of_others = range(1, 5)
original.id_of_others
```
```
(1, 2, 3, 4)
```

using standard tools
```python
from datetime import datetime
from time import sleep

from pyhandling import close, operation_by, eventually, returnly
from sculpting import read_only_attribute_map_as
from sculpting.tools import once


standard_tool_sculpture_from = (
    close(Sculpture)(
        id=read_only_attribute_map_as((getattr |by| 'id') |then>> operation_by('*', 2)),
        creation_time=once(eventually(datetime.now))
    )
    |then>> returnly(getattr |by| "creation_time")
)

standard_tool_sculpture = standard_tool_sculpture_from(original)
print(datetime.now().time(), "- at initialization")

sleep(3)

print(standard_tool_sculpture.creation_time.time(), "- at getting")
```
```
16:10:16.045444 - at initialization
16:10:16.045444 - at getting
```
