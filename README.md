# FileTrack

A Home Assistant custom component that monitors folders and exposes their total size as a sensor, along with file count and a `fileList` attribute. It is perfectly designed as a companion for the [Camera Gallery Card](https://github.com/TheScubaDiver/camera-gallery-card), but can also be used as a standalone integration.


## Installation

### HACS (Recommended)
1. Add this repository as a custom repository in HACS.
2. Download **FileTrack** via HACS.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration → FileTrack**. The setup completes instantly, no initial configuration needed.

---

## Usage & Configuration

How to create a sensor:

### Method 1 — FileTrack Integration
Open **Settings → Devices & Services → FileTrack → Configure** (gear icon). Select "Add new FileTrack sensor". Enter at least a name and folder path then click Submit.

<img width="444" height="470" alt="image" src="https://github.com/user-attachments/assets/94fae908-228c-4e1f-9da2-c17b4a8e1e54" />

### Method 2 — Camera Gallery Card
Sensors are created directly from the **[Camera Gallery Card](https://github.com/TheScubaDiver/camera-gallery-card) Editor** — no YAML, service calls, or manual setup required.

<img width="418" height="380" alt="image" src="https://github.com/user-attachments/assets/e0c5b505-f94b-48f8-b8a3-dbadee3cd41b" />

### Method 3 — YAML
Add sensors directly to your `configuration.yaml` file:

```yaml
filetrack:
  sensors:
    - folder: /config/www/snapshots
      filter: '*.jpg'
      name: Snapshots
      unique_id: snapshots_jpg
      sort: date
      recursive: true
```

#### YAML Configuration Variables

| Name | Type | Default | Description
| ---- | ---- | ------- | -----------
| name | string | **Required** | Friendly name for the sensor (used as the entity ID).
| folder | string | **Required** | Folder to scan. Must begin with `/config/www/<your-folder>`.
| filter | string | `*` | Glob pattern matched against filenames (e.g. `*.jpg`).
| unique_id | string | none | Custom unique_id so the entity can be customised/removed via the UI.
| sort | string | `date` | One of `name`, `date`, or `size`.
| recursive | boolean | `false` | If true, search every subfolder under `folder`, matching `filter` at any depth. **Note:** in deep trees this can be slow — keep `filter` specific (e.g. `*.jpg`) for large folders.

*Note1: Restart Home Assistant after adding YAML entries.*

*Note2: From FileTrack 2.0, the legacy YAML format (sensor: > platform: filetrack) is not supported. Follow the example above.*

---

## Removing Sensors

> 💡 Per-sensor removal lives **behind the gear icon**, not on the integration card itself — that part trips a lot of people up.

* **UI / service sensors:** Open **Settings → Devices & Services → FileTrack → Configure** (gear icon) → **Remove FileTrack sensors**. Tick the sensors you want gone and confirm.
* **YAML sensors:** Remove the relevant entries from your `configuration.yaml` and restart Home Assistant.
* **Remove the whole integration:** Use the **Delete** option on the FileTrack integration card. The sensor store is wiped automatically, so a future re-install starts clean instead of resurrecting old sensors.
