# Voice-Based Concept Understanding Analyser (VBCUA) 2.0
### *Major Project Edition — Multimodal Cognitive AI & Speech Prosody Examiner*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58%2B-FF4B4B.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/Pytest-Passing-brightgreen.svg)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

---

## 📌 Executive Summary & Motivation

**VBCUA 2.0** is an enterprise-grade multimodal artificial intelligence platform designed to evaluate oral conceptual explanations and technical communication. Moving far beyond traditional text-only similarity checkers, VBCUA integrates **speech acoustics, cognitive depth assessment, pedagogical rubric evaluation, factual misconception detection, and an adaptive AI Viva-Voce oral examiner**.

Developed as a flagship **Major Project (Capstone / Final Year Engineering)**, VBCUA addresses the critical gap in modern education and technical hiring: how to objectively measure **both depth of conceptual understanding and spoken delivery excellence** in real-time.

---

## 🌟 Key Innovations & Major Project Highlights

### 1. 🎙️ Zero-Friction Audio Ingestion Studio
- **Direct In-Browser Microphone Recording**: Powered by Streamlit's native `st.audio_input`, candidates can record oral explanations directly with a single click.
- **Multi-Format Audio Upload**: Supports `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg` files.
- **Pre-Loaded Benchmark Preset**: One-click instant testing using `samples/sample_machine_learning.wav`.
- **Manual Transcript Fallback**: Allows manual transcript edits for offline development or noisy audio environments.

### 2. 🧠 Bloom's Revised Taxonomy Cognitive Classifier
- Categorizes spoken explanations across 6 pedagogical cognitive levels:
  - **Level 1 (Remembering)**: Recalling basic terminology and definitions.
  - **Level 2 (Understanding)**: Explaining mechanisms and summarizing principles.
  - **Level 3 (Applying)**: Connecting theory with concrete real-world engineering use cases.
  - **Level 4 (Analyzing)**: Comparing paradigms, breaking down system architectures.
  - **Level 5 (Evaluating)**: Assessing tradeoffs, constraints, latency, and failure modes.
  - **Level 6 (Creating)**: Synthesizing end-to-end solutions and novel architectures.

### 3. 🕸️ 5-Axis Pedagogical Rubric & Radar Chart
Evaluates spoken answers across 5 independent academic dimensions (0-100%):
1. **Conceptual Accuracy & Definition** (Semantic similarity & terminology coverage)
2. **Technical Architecture & Mechanism** (Structural and pipeline explanation)
3. **Real-World Application & Examples** (Concrete industrial applications)
4. **Tradeoffs, Limitations & Edge Cases** (Critical analysis of bottlenecks)
5. **Delivery & Prosody** (Speech fluency, pacing, and confidence)

### 4. ⚠️ Factual Misconceptions & Anti-Pattern Detection
- Identifies common student misunderstandings (e.g. confusing Linear Regression with classification, assuming Unsupervised Learning uses labels, misinterpreting RAM as non-volatile, confusing SaaS with IaaS).
- Displays an immediate alert showing what the student said alongside the expert factual correction.

### 5. 🗺️ Concept Ontology & Knowledge Graph Coverage
- Compares spoken terminology against reference ontologies and subtopics.
- Highlights **Demonstrated Concepts (Green badges)** vs **Omitted Terminology (Red badges)** to pinpoint knowledge gaps.

### 6. 🗣️ Speech Prosody & Acoustic Intelligence
- **Speaking Rate (WPM)**: Calculates Words Per Minute with zone feedback (*Sluggish < 110*, *Optimal 110-165*, *Rushed > 165 WPM*).
- **Pitch Cadence & Expressiveness (Hz)**: Measures fundamental frequency variation to distinguish monotone delivery from engaging modulation.
- **Hesitation & Pause Analytics**: Distinguishes rhetorical pauses from prolonged hesitation blocks.
- **Dual Visualizations**: Real-time **Waveform** and **Frequency Spectrogram** (Mel formants).

### 7. 🎓 Adaptive Viva-Voce (AI Oral Examiner Mode)
- Automatically analyzes omissions and cognitive level to formulate 3 targeted follow-up viva questions:
  - *Clarification Question* (testing missed foundational terms)
  - *Analytical Deep-Dive* (probing internal mechanics)
  - *Edge Case / Scenario Challenge* (testing real-world tradeoff handling)
- Supports interactive candidate responses directly in the dashboard.

### 8. 📄 Publication-Grade Multi-Page PDF Diagnostic Report
- Generates a 3-page executive diagnostic report with high-resolution radar charts, cognitive badges, prosody metrics, ontology coverage, viva questions, and full transcript.

---

## 🏛️ System Architecture

```text
+--------------------------------------------------------------------------------------------------+
|                                    VBCUA 2.0 SYSTEM ARCHITECTURE                                 |
+--------------------------------------------------------------------------------------------------+

       [ Oral Explanation ]
                |
                +---> Direct Microphone (st.audio_input)
                |---> Audio Upload (WAV, MP3, M4A, OGG)
                +---> Included Preset Audio Sample
                                |
                                v
               [ Audio Signal & Feature Pipeline ]
               * Waveform & Spectrogram Processing
               * Duration, RMS Energy & Zero-Crossing Rate
               * Speaking Rate (WPM) & Pitch Expressiveness (Hz)
                                |
                                v
                [ Automatic Speech Recognition ]
                * OpenAI Whisper (or Manual Fallback)
                * Filler Words & Hesitation Analysis
                                |
                                v
             +------------------+------------------+
             |                                     |
             v                                     v
   [ Cognitive AI Engine ]               [ Semantic Reasoning ]
   * Bloom's Taxonomy Classifier         * Sentence-BERT Similarity
   * Misconception Detector              * Lexical Cosine Fallback
   * Concept Ontology Coverage           * Key Term Coverage
             |                                     |
             +------------------+------------------+
                                |
                                v
                 [ Pedagogical Rubric Engine ]
                 * 5-Axis Spider / Radar Chart
                 * Overall Understanding & Fluency Scoring
                 * Adaptive Viva-Voce Question Formulator
                                |
                                v
               +----------------+----------------+
               |                                 |
               v                                 v
     [ Streamlit Dashboard ]             [ ReportLab Engine ]
     * 6 Interactive Tabs                * 3-Page Executive PDF
     * Historical Analytics              * SQLite Database Storage
```

---

## 📚 Multi-Domain Curriculum Bank

VBCUA 2.0 comes pre-configured with categorized academic domains and rich subtopic ontologies:

1. **AI & Machine Learning**:
   - Machine Learning (*Supervised, Unsupervised, Loss Function, Regularization*)
   - Deep Neural Networks (*Forward/Backprop, Activation Functions, Vanishing Gradients*)
   - Artificial Intelligence (*Knowledge Representation, Cognitive Systems, Ethics*)
2. **Cloud & Systems**:
   - Cloud Computing (*IaaS/PaaS/SaaS, Elasticity, Virtualization, Cloud Security*)
   - Operating Systems (*CPU Scheduling, Virtual Memory, IPC, Deadlocks*)
   - Microservices Architecture (*API Gateway, Service Discovery, Fault Tolerance*)
3. **Databases & Data Engineering**:
   - Database Management Systems (*Relational Algebra, Query Optimization, Indexing*)
   - ACID Transactions (*Two-Phase Locking, Write-Ahead Logging, Isolation Levels*)
4. **Networking & Software**:
   - Computer Networks & TCP/IP (*Three-Way Handshake, Flow Control, Routing*)
5. **Custom Concept Studio**:
   - Allows educators or candidates to enter any custom topic and reference text for instant automated evaluation.

---

## 💻 Tech Stack

- **Frontend & UI**: Streamlit 1.58+, Altair, HTML5 / CSS Custom Components
- **Backend & REST API**: FastAPI, Uvicorn, Pydantic, Python-Multipart
- **Speech & Audio**: Librosa, SoundFile, NumPy, Wave, Audioop, PyDub / Matplotlib Spectrograms
- **Speech-to-Text**: OpenAI Whisper
- **NLP & Semantics**: Sentence-Transformers, PyTorch, NLTK
- **Document & Graphic Generation**: ReportLab 5.0, Matplotlib
- **Database & Storage**: SQLite3 with automatic schema migration
- **Testing & Quality Assurance**: Pytest 9.1+

---

## 🚀 Installation & Getting Started

### 1. Clone & Set Up Environment
```powershell
# Clone the repository
git clone https://github.com/LOKESHBOOTU/Voice-Based-Concept-Understanding-Analyser.git
cd Voice-Based-Concept-Understanding-Analyser

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard
```powershell
streamlit run app.py
```
Open your browser at:
```text
http://127.0.0.1:8501
```

### 3. Launch the FastAPI Service
```powershell
uvicorn api:app --reload --port 8000
```
Explore the interactive Swagger API documentation at:
```text
http://127.0.0.1:8000/docs
```

---

## 📡 REST API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and version |
| `GET` | `/domains` | List available curriculum domains |
| `GET` | `/concepts` | List concept titles, domain tags, key terms, and subtopics |
| `GET` | `/analytics` | Aggregate student cohort analytics & average scores |
| `GET` | `/results/recent` | Fetch historical evaluation records |
| `POST` | `/evaluate` | Multimodal audio analysis (returns JSON with cognitive & prosody metrics, optional PDF) |
| `GET` | `/report/{result_id}` | Download generated publication-grade PDF report |

---

## 🧪 Automated Test Suite

Run the full pytest suite:
```powershell
pytest
```
*Output: 15 passed across unit and integration tests (Bloom's taxonomy, rubrics, prosody, misconceptions, knowledge graph, viva engine, reporting, and database storage).*

---

## 🎓 Academic Defense & Presentation Tips

When presenting this project to an evaluation committee or interview panel:
1. **Highlight the Multimodal Advantage**: Emphasize that standard AI checks only grammar or keywords, while VBCUA evaluates **conceptual understanding, cognitive depth (Bloom's), and speech prosody (WPM, pitch expressiveness)**.
2. **Demonstrate Live Voice Recording**: Use the browser microphone feature in front of the panel to record a 30-second explanation of Machine Learning or Cloud Computing.
3. **Showcase the 5-Axis Radar Chart**: Walk through how the explanation scored on Accuracy vs Architecture vs Application vs Tradeoffs vs Delivery.
4. **Trigger the Misconception Detector**: Intentionally mention a misconception (e.g. *"linear regression is used for classification"*) to showcase real-time error catching.
5. **Demonstrate Adaptive Viva-Voce**: Show how the AI immediately formulates 3 oral exam questions based on what you omitted.
6. **Download the PDF Report**: Present the multi-page branded PDF report as proof of ready-to-deploy assessment technology.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
