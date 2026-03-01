# Klayout3D

**Klayout3D** is a Python-based toolkit that enables real-time 3D visualization of GDSII layouts directly from KLayout. Designed for photonics workflows, it bridges KLayout's layout editor with an interactive 3D rendering engine — allowing engineers and designers to instantly visualize selected layout regions as three-dimensional structures.

---

## How It Works

Klayout3D runs as a local server that communicates with a KLayout macro. Once the server is running, you can select one or more cells (boxes) within your open GDS layout in KLayout and trigger the macro to send the geometry data to the server. A 3D plot is then generated and displayed automatically in your browser.

The tool supports layer-based extrusion using a technology file, overlap detection, and triangulation to produce accurate 3D geometry from 2D layout data.

---

## Getting Started

### 1. Install Dependencies

```bash
pip install -r Requirement.txt
```

### 2. Set Up the KLayout Macro

1. Open KLayout and navigate to **Macros → Macro Development**.
2. Create a new macro and paste the contents of `KLayoutPart/Macro.py` into it.
3. Save and assign a shortcut or toolbar button to the macro for convenience.

### 3. Start the Local Server

```bash
python Main.py
```

This launches the local server that listens for geometry data from the KLayout macro.

### 4. Visualize Your Layout in 3D

1. Open your GDS file in KLayout.
2. Select one or more cells (boxes) you want to visualize.
3. Run the macro — it will send the selected geometry to the server.
4. The 3D visualization will appear automatically in your browser.

---

## Customization

### Technology File

The technology file (`Example/TechnologyExample.json`) defines how GDS layers are mapped to 3D structures. Edit this file to match your fabrication process stack.

---
