# Architecture
Each application within Twenty Forty Eight OS provides 4 components:
1. Metadata: Describes the application, name, version, icon (base64 strin of 16x16 icon), etc.
2. A JSON DSL that describes the applications configuration and how to generate its web interface
3. A config file that the DSL generates on form submission
4. A scene or group of scenes that will be rendered by the application on the LED matrix

## Metadata
The metadata is a JSON file that describes the application. It contains the following fields:

| Field | Description |
| ----- | ----------- |
| name | The name of the application |
| version | The version of the application |
| icon | The icon of the application |
| description | A description of the application |
| author | The author of the application |

## JSON DSL
The JSON DSL is a JSON file that describes the application configuration and how to generate its web interface.

Each setting has a name, a label, and a type. The type is one of the following:
- dropdown
- select
- text
- checkbox
- radio
- slider

The label is the text that will be displayed next to the setting.

### Dropdown
A dropdown is a list of options that can be selected by the user.

| Field | Description |
| ----- | ----------- |
| options | An array of options |
| default | The default value of the setting |

### Select
A select is a list of options that can be selected by the user.

| Field | Description |
| ----- | ----------- |
| options | An array of options |
| default | The default value of the setting |

### Text
A text setting is a single line of text that can be entered by the user.

| Field | Description |
| ----- | ----------- |
| default | The default value of the setting |

### Checkbox
A checkbox is a setting that can be either true or false.

| Field | Description |
| ----- | ----------- |
| default | The default value of the setting |

### Radio
A radio is a setting that is picked from a list of options.

| Field | Description |
| ----- | ----------- |
| options | An array of options |
| default | The default value of the setting |

## Slider
A slider is a setting that can be set to a value between a minimum and maximum value.

| Field | Description |
| ----- | ----------- |
| min | The minimum value of the slider |
| max | The maximum value of the slider |
| default | The default value of the setting |

## Setting Groups
Setting groups are a way to group settings together. They are used to group settings that are related to each other.
For example, a setting group can be used to group settings that are related to a specific scene.

| Field | Description |
| ----- | ----------- |
| name | The name of the setting group |
| settings | An array of settings |

## Example JSON DSL

Description of an example application that has a dropdown, a slider, and a text setting.
```json
{
  "name": "Example",
  "version": "1.0.0",
  "icon": "---",
  "description": "An example application",
  "author": "me",
  "settings": [
    {
      "name": "scene",
      "label": "Scene",
      "type": "dropdown",
      "options": [
        "scene1",
        "scene2",
        "scene3"
      ],
      "default": "scene1"
    },
    {
      "name": "brightness",
      "label": "Brightness",
      "type": "slider",
      "min": 0,
      "max": 100,
      "default": 50
    },
    {
      "name": "color",
      "label": "Color",
      "type": "text",
      "default": "#ff0000"
    }
  ]
}
```
Config generated from the above JSON DSL:
```json
{
  "scene": "scene1",
  "brightness": 50,
  "color": "#ff0000"
}
```

## Config File
The config file is generated from the JSON DSL on form submission, and applications should include an example config file that will be loaded by default.
