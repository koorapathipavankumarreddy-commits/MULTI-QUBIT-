import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import Axes3D
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace
from qiskit.visualization import plot_bloch_multivector, plot_state_city, plot_state_hinton
import io
import re

st.set_page_config(page_title="Multi-Qubit State Visualizer", layout="wide")

st.title("🔬 Multi-Qubit State Visualizer")
st.markdown("**Input:** Define your quantum state • **Output:** Circle notation, Dirac notation, Bloch spheres, probabilities")

INPUT_MODE = st.sidebar.radio("Input Mode", [
    "🎯 Statevector (amplitudes)",
    "🔧 Quantum Circuit (gates)",
    "📐 Bloch Angles (θ, φ per qubit)",
    "📝 Dirac Notation (text)"
], index=0)

NUM_QUBITS = st.sidebar.selectbox("Number of Qubits", [2, 3], index=0)

def parse_statevector_input(text, n):
    """Parse comma-separated complex amplitudes: 0.707, 0, 0, 0.707"""
    try:
        parts = [p.strip() for p in text.split(',')]
        if len(parts) != 2**n:
            return None, f"Expected {2**n} amplitudes for {n} qubits, got {len(parts)}"
        amps = []
        for p in parts:
            p = p.replace(' ', '').replace('i', 'j')
            if 'j' not in p and p not in ['0', '1', '-1']:
                p += '+0j'
            amps.append(complex(p))
        amps = np.array(amps, dtype=complex)
        norm = np.linalg.norm(amps)
        if abs(norm - 1.0) > 1e-6:
            amps = amps / norm
            return Statevector(amps), f"Normalized (original norm: {norm:.4f})"
        return Statevector(amps), "Valid statevector"
    except Exception as e:
        return None, f"Parse error: {e}"

def parse_dirac_input(text, n):
    """Parse Dirac notation like: 0.707|00> + 0.707|11>"""
    try:
        text = text.replace('⟩', '>').replace('⟨', '<').replace('|', '')
        terms = re.split(r'\s*\+\s*', text)
        amps = np.zeros(2**n, dtype=complex)
        for term in terms:
            term = term.strip()
            match = re.match(r'([\d\.\+\-j]+)\s*>\s*(\d+)', term.replace('>', '>'))
            if not match:
                match = re.match(r'([\d\.\+\-j]+)\s*(\d+)', term)
            if match:
                coeff_str, basis = match.groups()
                coeff = complex(coeff_str.replace('i', 'j'))
                idx = int(basis, 2)
                amps[idx] = coeff
        norm = np.linalg.norm(amps)
        if norm > 1e-10:
            amps = amps / norm
        return Statevector(amps), "Parsed from Dirac notation"
    except Exception as e:
        return None, f"Parse error: {e}"

def parse_bloch_angles(angles_text, n):
    """Parse θ,φ pairs per qubit: q0: 1.57, 0; q1: 1.57, 3.14"""
    try:
        amps = np.zeros(2**n, dtype=complex)
        qubit_states = []
        for q in range(n):
            pattern = rf'q{q}\s*[:=]\s*([\d\.\-]+)\s*[,;]\s*([\d\.\-]+)'
            match = re.search(pattern, angles_text)
            if not match:
                return None, f"Missing angles for qubit {q} (format: q{q}: θ, φ)"
            theta, phi = float(match.group(1)), float(match.group(2))
            a0 = np.cos(theta/2)
            a1 = np.sin(theta/2) * np.exp(1j * phi)
            qubit_states.append([a0, a1])
        
        # Tensor product
        state = qubit_states[0]
        for q in range(1, n):
            state = np.kron(state, qubit_states[q])
        return Statevector(state), "Built from Bloch angles"
    except Exception as e:
        return None, f"Parse error: {e}"

def build_circuit_from_gates(gate_list, n):
    """Build circuit from list of gate dicts"""
    circuit = QuantumCircuit(n)
    for gate_info in gate_list:
        gate = gate_info['gate']
        target = gate_info['target']
        control = gate_info.get('control')
        angle = gate_info.get('angle', 0)
        
        if gate == "X": circuit.x(target)
        elif gate == "Y": circuit.y(target)
        elif gate == "Z": circuit.z(target)
        elif gate == "H": circuit.h(target)
        elif gate == "S": circuit.s(target)
        elif gate == "T": circuit.t(target)
        elif gate == "RX": circuit.rx(angle, target)
        elif gate == "RY": circuit.ry(angle, target)
        elif gate == "RZ": circuit.rz(angle, target)
        elif gate == "CNOT": circuit.cx(control, target)
        elif gate == "CZ": circuit.cz(control, target)
    return Statevector.from_instruction(circuit)

def dirac_notation(statevector):
    n = statevector.num_qubits
    terms = []
    for i, amp in enumerate(statevector.data):
        if abs(amp) > 1e-10:
            basis = format(i, f'0{n}b')
            if abs(amp.imag) < 1e-10:
                coeff = f"{amp.real:.4f}"
            elif abs(amp.real) < 1e-10:
                coeff = f"{amp.imag:.4f}i"
            else:
                sign = '+' if amp.imag >= 0 else '-'
                coeff = f"{amp.real:.4f} {sign} {abs(amp.imag):.4f}i"
            terms.append(f"{coeff}|{basis}⟩")
    return " + ".join(terms) if terms else "0"

def plot_circle_notation(statevector):
    n = statevector.num_qubits
    fig, axes = plt.subplots(1, n, figsize=(4*n, 4))
    if n == 1:
        axes = [axes]
    
    for q in range(n):
        rho = partial_trace(DensityMatrix(statevector), [i for i in range(n) if i != q])
        bloch = np.array([
            2 * np.real(rho.data[0,1]),
            2 * np.imag(rho.data[0,1]),
            np.real(rho.data[0,0] - rho.data[1,1])
        ])
        theta = np.arccos(np.clip(bloch[2], -1, 1))
        phi = np.arctan2(bloch[1], bloch[0])
        
        ax = axes[q]
        circle = Circle((0, 0), 1, fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(circle)
        
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        
        ax.arrow(0, 0, x, y, head_width=0.08, head_length=0.08, fc='#e74c3c', ec='#e74c3c', linewidth=3)
        ax.plot([0, x], [0, y], 'r--', alpha=0.4)
        
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect('equal')
        ax.set_title(f"Qubit {q}\nθ={theta:.3f}, φ={phi:.3f}", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.2)
        ax.axvline(x=0, color='gray', linestyle='-', alpha=0.2)
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.set_yticks([-1, -0.5, 0, 0.5, 1])
    
    plt.tight_layout()
    return fig

def plot_probabilities(statevector):
    probs = statevector.probabilities()
    basis_states = [format(i, f'0{statevector.num_qubits}b') for i in range(len(probs))]
    return basis_states, probs

# ============================================================
# INPUT SECTION
# ============================================================
st.header("📥 Input")

statevector = None
input_status = ""

if INPUT_MODE == "🎯 Statevector (amplitudes)":
    st.markdown(f"Enter **{2**NUM_QUBITS} complex amplitudes** (comma-separated, auto-normalized):")
    default_vec = "0.707, 0, 0, 0.707" if NUM_QUBITS == 2 else "0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5"
    vec_input = st.text_area("Amplitudes", value=default_vec, height=80, 
        help="Examples: 1,0,0,0 (|00⟩) | 0.707,0,0,0.707 (Bell) | 0.5,0.5,0.5,0.5 (|++⟩)")
    statevector, input_status = parse_statevector_input(vec_input, NUM_QUBITS)

elif INPUT_MODE == "📝 Dirac Notation (text)":
    st.markdown(f"Enter state in **Dirac notation** (e.g., `0.707|00> + 0.707|11>`):")
    default_dirac = "0.707|00> + 0.707|11>" if NUM_QUBITS == 2 else "0.5|000> + 0.5|011> + 0.5|101> + 0.5|110>"
    dirac_input = st.text_input("Dirac notation", value=default_dirac)
    statevector, input_status = parse_dirac_input(dirac_input, NUM_QUBITS)

elif INPUT_MODE == "📐 Bloch Angles (θ, φ per qubit)":
    st.markdown("Enter **θ, φ** for each qubit (radians):")
    default_angles = "q0: 1.57, 0; q1: 1.57, 0" if NUM_QUBITS == 2 else "q0: 1.57, 0; q1: 1.57, 0; q2: 1.57, 0"
    angles_input = st.text_input("Bloch angles", value=default_angles,
        help="Format: q0: θ, φ; q1: θ, φ; ... | θ∈[0,π], φ∈[0,2π]")
    statevector, input_status = parse_bloch_angles(angles_input, NUM_QUBITS)

elif INPUT_MODE == "🔧 Quantum Circuit (gates)":
    st.markdown("Build a circuit gate by gate:")
    gate_options = ["I", "X", "Y", "Z", "H", "S", "T", "RX", "RY", "RZ", "CNOT", "CZ"]
    num_gates = st.number_input("Number of gates", 1, 15, 3)
    
    gate_list = []
    for i in range(num_gates):
        cols = st.columns([2, 1, 1, 1.5])
        with cols[0]:
            gate = st.selectbox(f"Gate {i+1}", gate_options, key=f"gate_{i}")
        with cols[1]:
            target = st.selectbox(f"Target", list(range(NUM_QUBITS)), key=f"t_{i}")
        with cols[2]:
            if gate in ["CNOT", "CZ"]:
                control = st.selectbox(f"Control", [q for q in range(NUM_QUBITS) if q != target], key=f"c_{i}")
            else:
                control = None
        with cols[3]:
            angle = st.number_input(f"Angle", value=0.0, step=0.1, key=f"a_{i}") if gate in ["RX","RY","RZ"] else 0
        
        gate_list.append({'gate': gate, 'target': target, 'control': control, 'angle': angle})
    
    if st.button("Build Circuit", type="primary"):
        statevector = build_circuit_from_gates(gate_list, NUM_QUBITS)
        input_status = "Circuit built successfully"
    else:
        statevector = Statevector.from_label('0'*NUM_QUBITS)
        input_status = "Click 'Build Circuit' to generate"

# Status
if input_status:
    if "error" in input_status.lower() or "parse" in input_status.lower():
        st.error(input_status)
    else:
        st.success(f"✅ {input_status}")

# ============================================================
# OUTPUT SECTION
# ============================================================
if statevector is not None:
    st.divider()
    st.header("📤 Output")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔵 Circle Notation", 
        "📝 Dirac Notation", 
        "🌐 Bloch Spheres (3D)", 
        "📊 Probabilities", 
        "🏙️ City/Hinton Plot"
    ])
    
    with tab1:
        st.subheader("Circle Notation (2D Bloch Circles)")
        fig = plot_circle_notation(statevector)
        st.pyplot(fig)
        st.caption("Red arrow = Bloch vector projection on XY plane. θ = polar angle, φ = azimuthal angle.")
    
    with tab2:
        st.subheader("Dirac Notation")
        dirac = dirac_notation(statevector)
        st.latex(f"|\\psi\\rangle = {dirac.replace('|', '\\vert ').replace('⟩', '\\rangle')}")
        st.code(dirac, language="text")
        
        st.subheader("Amplitude Details")
        for i, amp in enumerate(statevector.data):
            if abs(amp) > 1e-10:
                basis = format(i, f'0{NUM_QUBITS}b')
                st.write(f"|{basis}⟩:  {amp.real:+.4f} {amp.imag:+.4f}i  |  mag={abs(amp):.4f}  phase={np.angle(amp):+.4f}")
    
    with tab3:
        st.subheader("Bloch Spheres (Qiskit 3D)")
        fig_bloch = plot_bloch_multivector(statevector)
        st.pyplot(fig_bloch)
    
    with tab4:
        st.subheader("Measurement Probabilities")
        basis, probs = plot_probabilities(statevector)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            fig, ax = plt.subplots(figsize=(8, 4))
            bars = ax.bar(basis, probs, color='#3498db', edgecolor='#2980b9', width=0.6)
            ax.set_ylabel("Probability")
            ax.set_xlabel("Basis State")
            ax.set_ylim(0, 1.1)
            ax.grid(axis='y', alpha=0.3)
            for bar, p in zip(bars, probs):
                if p > 0.01:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                           f'{p:.3f}', ha='center', va='bottom', fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.markdown("**Table**")
            for b, p in zip(basis, probs):
                if p > 1e-6:
                    st.write(f"|{b}⟩:  **{p:.4f}** ({p*100:.1f}%)")
            st.markdown(f"**Sum: {np.sum(probs):.6f}**")
    
    with tab5:
        st.subheader("State Visualization")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**City Plot** (magnitude)")
            fig_city = plot_state_city(statevector)
            st.pyplot(fig_city)
        with col2:
            st.markdown("**Hinton Plot** (real/imag)")
            fig_hinton = plot_state_hinton(statevector)
            st.pyplot(fig_hinton)
    
    # Export
    st.divider()
    st.subheader("📥 Export")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("Download Statevector (JSON)", 
            data=str({f"|{format(i,f'0{NUM_QUBITS}b')}⟩": complex(amp) for i,amp in enumerate(statevector.data)}),
            file_name="statevector.json")
    with col2:
        st.download_button("Download Dirac Notation", 
            data=dirac_notation(statevector), file_name="dirac.txt")
    with col3:
        st.download_button("Download Probabilities (CSV)", 
            data="\n".join([f"|{b}⟩,{p}" for b,p in zip(basis, probs)]),
            file_name="probabilities.csv")

else:
    st.info("👆 Provide input above to generate visualizations")

# Sidebar info
st.sidebar.divider()
st.sidebar.markdown("### Quick Presets")
if st.sidebar.button("|00⟩ (Ground)"):
    st.rerun()
if st.sidebar.button("|++⟩ (All +)"):
    st.rerun()
if st.sidebar.button("Bell |Φ⁺⟩"):
    st.rerun()
if st.sidebar.button("GHZ (3q)"):
    st.rerun()
if st.sidebar.button("W State (3q)"):
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("Built with Streamlit + Qiskit + Matplotlib")