# Multi-Qubit State Visualizer

An interactive Streamlit application for visualizing quantum states with multiple input methods and rich visualizations.

## Features

### Input Methods
- **Statevector Amplitudes** - Enter complex amplitudes directly (auto-normalized)
- **Quantum Circuit Builder** - Drag-and-drop style gate selection (H, X, Y, Z, RX, RY, RZ, CNOT, CZ, S, T)
- **Bloch Angles** - Define θ, φ per qubit
- **Dirac Notation** - Text input like `0.707|00> + 0.707|11>`

### Visualizations
| Tab | Description |
|-----|-------------|
| 🔵 Circle Notation | 2D Bloch circle projections per qubit with θ, φ angles |
| 📝 Dirac Notation | Full state in bra-ket notation + amplitude details |
| 🌐 Bloch Spheres | Qiskit's 3D interactive Bloch sphere visualization |
| 📊 Probabilities | Bar chart + table of measurement probabilities |
| 🏙️ City/Hinton Plot | Magnitude (city) and real/imaginary (hinton) views |

### Exports
- Statevector as JSON
- Dirac notation as text
- Probabilities as CSV

### Quick Presets
- `|00⟩` (Ground state)
- `|++⟩` (All + superposition)
- Bell state `|Φ⁺⟩`
- GHZ state (3 qubit)
- W state (3 qubit)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

Open browser to `http://localhost:8501`

## Requirements
- Python 3.8+
- streamlit ≥ 1.28.0
- qiskit ≥ 0.45.0
- matplotlib ≥ 3.7.0
- numpy ≥ 1.24.0

## Example Inputs

**2-qubit Bell state:**
```
Statevector: 0.707, 0, 0, 0.707
Dirac: 0.707|00> + 0.707|11>
Bloch: q0: 1.57, 0; q1: 1.57, 0
```

**3-qubit GHZ:**
```
Statevector: 0.707, 0, 0, 0, 0, 0, 0, 0.707
Dirac: 0.707|000> + 0.707|111>
```

## Project Structure
```
Qc/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── streamlit.log       # Runtime logs
```

## Screenshots

Run the app and explore each tab to see visualizations for different quantum states.

## License
MIT